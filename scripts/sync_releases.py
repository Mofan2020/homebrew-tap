#!/usr/bin/env python3
"""把 tap 里的每个 cask 更新到对应项目的**最新正式版**。

**这个脚本只认正式版。** GitHub 的 ``/releases/latest`` 端点返回的是最近
一个「不是 draft、不是 pre-release」��发布，所以问它就够了 —— 不用自己去
翻 ``/releases`` 列表再挑。规则写在 ``check_stable_only.py`` 里，这里是
另一道闸：脚本自己产出的东西天然满足那条规则。

**它会做什么。** 对每个 cask：

1. 从 ``homepage`` 取出上游仓库，问它最新正式版是哪个 tag。
2. tag 跟 cask 里现在的版本一样 → 什么都不做。
3. 不一样 → 按 cask 里的 url 模板拼出资产名，去 release 的资产列表里找。
   找得到就下载、现算 sha256、改写 cask 的 version 和 sha256。
4. 资产名对不上（上游改了文件命名）→ 在资产列表里按文件名相似度找。
   只有一个明显候选才用；拿不准就**跳过这个 cask**，不动它。

**它不会做什么。** 应用名、bundle id 这类东西脚本猜不出来（上游改名了
app 叫别的名字，只有把 dmg 挂上才知道）。改了名字的版本要人来改。

用法::

    python3 scripts/sync_releases.py            # 更新，报告改了哪些
    python3 scripts/sync_releases.py --check    # 只报告，不改文件
    python3 scripts/sync_releases.py --cask skycmedia   # 只处理一个

退出码 0 表示「该更的都更了，或者没什么可更的」。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASKS = sorted((ROOT / "Casks").glob("*.rb"))

VERSION_RE = re.compile(r'^\s*version\s+"([^"]+)"', re.MULTILINE)
HOMEPAGE_RE = re.compile(
    r'^\s*homepage\s+"https://github\.com/([^/"]+)/([^/"]+)"', re.MULTILINE
)
SHA_RE = re.compile(r'^\s*sha256\s+"([0-9a-fA-F]{64})"', re.MULTILINE)
URL_RE = re.compile(r'^\s*url\s+"([^"]+)"', re.MULTILINE)

#: 架构块。``on_arm do`` / ``on_intel do`` 里的 url 和 sha256 是一对。
ARCH_BLOCKS = ("on_arm", "on_intel")


class Cask:
    """一个 cask 文件里跟版本有关的那几样东西。"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.text = path.read_text(encoding="utf-8")
        self.lines = self.text.split("\n")

        versions = VERSION_RE.findall(self.text)
        homepages = HOMEPAGE_RE.findall(self.text)
        if not versions:
            raise ValueError(f"{path.name}: 没有 version")
        if not homepages:
            raise ValueError(f"{path.name}: 没有指向 GitHub 的 homepage")
        self.version = versions[0]
        self.owner, self.repo = homepages[0]

        self.slots = self._parse_slots()

    def _parse_slots(self) -> list[dict]:
        """找出每个 url 和它对应的 sha256。

        cask 里 url 和 sha256 的排法有两种：顶层的（``version`` 下面直接
        一对）和架构块里的（``on_arm do`` ... ``end``）。两种都得认。
        """
        slots: list[dict] = []
        context: list[str] = []
        pending_sha: tuple[int, str] | None = None

        for index, line in enumerate(self.lines):
            stripped = line.strip()

            block = re.match(r"^(on_arm|on_intel)\s+do$", stripped)
            if block:
                context.append(block.group(1))
                pending_sha = None
                continue

            if stripped == "end":
                # 只有架构块会往栈里压东西，别的块（livecheck）的 end
                # 不动这个栈。
                if context:
                    context.pop()
                pending_sha = None
                continue

            sha = re.match(r'^sha256\s+"([0-9a-fA-F]{64})"$', stripped)
            if sha:
                pending_sha = (index, sha.group(1).lower())
                continue

            url = URL_RE.match(stripped)
            if url:
                template = url.group(1)
                arch = context[-1] if context else ""
                slots.append(
                    {
                        "index": index,
                        "template": template,
                        "arch": arch,
                        "sha_index": pending_sha[0] if pending_sha else None,
                        "sha": pending_sha[1] if pending_sha else "",
                    }
                )
                pending_sha = None

        if not slots:
            raise ValueError(f"{self.path.name}: 没有 url")
        return slots

    @property
    def name(self) -> str:
        return self.path.stem


# --------------------------------------------------------------------- GitHub


def _request(url: str, accept: str = "application/vnd.github+json") -> bytes:
    """问 GitHub 要一个 URL 的内容。

    **优先用 ``gh``。** 本机的 Python 不一定认得 HTTPS 中间人那张根证书
    （urllib 直接问 api.github.com 会报 certificate verify failed），而
    ``gh`` 用的是另一套证书链，通的。CI 里同样有 ``gh``。
    """
    if shutil.which("gh"):
        endpoint = url.split("https://api.github.com/", 1)[-1]
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return result.stdout.encode("utf-8")
        if "Not Found" in result.stderr or "HTTP 404" in result.stderr:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        raise RuntimeError(result.stderr.strip() or "gh api 失败")

    request = urllib.request.Request(url, headers={"Accept": accept})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def latest_stable(owner: str, repo: str) -> dict | None:
    """上游最新**正式版**的 release。拿不到就返回 None。"""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        return json.loads(_request(url))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # 一个正式版都没有。
            return None
        raise


# ------------------------------------------------------------------ 资产匹配


def _tokens(name: str) -> set[str]:
    """把文件名拆成「有意义的词」。

    版本号那种（``0.6.1``、``v1.2``）不参与比较 —— 它们本来就该变。
    """
    parts = re.split(r"[-._]", name.lower())
    return {p for p in parts if p and not p.isdigit() and not re.fullmatch(r"v\d+", p)}


def _shape(name: str) -> tuple[str, ...]:
    """资产的「形状」：架构 + 格式。

    ``NeteaseMusicDownloader-macOS-arm64.dmg`` 和
    ``SkycMedia-macOS-arm64.dmg`` 形状一样（都是 macOS + arm64 + dmg），
    只有产品名前缀换了 —— 上游改名时资产名就会这样变。

    比的是**后缀**那几个词：产品名可以换，架构和格式不能换。
    """
    parts = re.split(r"[-._]", name.lower())
    keep = [
        p for p in parts
        if p and not p.isdigit() and not re.fullmatch(r"v\d+", p)
    ]
    # 去掉第一个词（产品名），剩下的就是形状。
    return tuple(sorted(keep[1:])) if len(keep) > 1 else tuple()


def pick_asset(release: dict, slot: dict, new_version: str) -> str | None:
    """在 release 的资产列表里找出这个 url 模板该用哪个文件。

    先按模板直接拼（上游没改名字时永远命中）；拼不上再在列表里找形状
    一样的。拿不准就返回 None —— **宁可不动，也不要指错文件**。
    """
    assets = [a["name"] for a in release.get("assets", [])]
    if not assets:
        return None

    # 模板里的 #{version} 换成新版本号，剩下的就是资产名。
    candidate = slot["template"].split("#{version}")[-1].split("/")[-1]
    candidate = candidate.replace("#{version}", new_version)
    if candidate in assets:
        return candidate

    # 模板里带版本号的那种（HexoMan-#{version}-macos.zip），拼出来还是
    # 对得上，因为上面已经替换过了。
    old_name = slot["template"].split("#{version}")[-1].split("/")[-1]
    old_name = old_name.replace("#{version}", slot.get("old_version", ""))

    shape = _shape(old_name)
    if not shape:
        return None
    matches = [name for name in assets if _shape(name) == shape]
    if len(matches) == 1:
        return matches[0]
    return None


def sha256_of(url: str) -> str:
    """下载一个文件并现算 sha256。

    **一律现算。** 手抄 sha256 抄错过一次，抄进去一个西里尔字母，
    brew 要等到安装的时候才报错。
    """
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=600) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_of_asset(release: dict, asset_name: str, repo_full: str) -> str:
    """下 release 里的某个资产，算 sha256。

    **用 ``gh`` 下，不用 urllib。** 本机的 Python 不认得 HTTPS 中间人那张
    根证书（urllib 直接问 api.github.com 会报 certificate verify failed），
    而 ``gh`` 用的是另一套证书链，通的。CI 里同样有 ``gh``。

    走 ``gh api`` 的 assets 端点而不是 browser_download_url：后者会跳到
    objects.githubusercontent.com，那里不一定认得本机的证书链。
    """
    for asset in release.get("assets", []):
        if asset["name"] != asset_name:
            continue
        asset_id = asset.get("id")
        if not asset_id:
            continue
        if shutil.which("gh"):
            result = subprocess.run(
                [
                    "gh", "api",
                    f"repos/{repo_full}/releases/assets/{asset_id}",
                    "--header", "Accept: application/octet-stream",
                ],
                capture_output=True,
                timeout=900,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"下载 {asset_name} 失败："
                    f"{result.stderr.decode('utf-8', 'replace').strip()}"
                )
            return hashlib.sha256(result.stdout).hexdigest()

        url = asset["browser_download_url"]
        request = urllib.request.Request(url)
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        digest = hashlib.sha256()
        with urllib.request.urlopen(request, timeout=600) as response:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    raise LookupError(f"资产 {asset_name} 不在 release 里")


# --------------------------------------------------------------------- 改写


def _indent_of(line: str) -> str:
    """一行前面的空格。"""
    match = re.match(r"^\s*", line)
    return match.group(0) if match else ""


def rewrite(cask: Cask, new_version: str, shas: dict[int, str],
            urls: dict[int, str]) -> str:
    """产出改好的 cask 文本。

    只改四样东西：version 那一行、每个 sha256、每个 url。别的行一个字
    都不动。

    **缩进跟着原来那行走。** cask 里有两种排法：顶层的
    （``version`` 下面直接一对 sha256 和 url）和架构块里的
    （``on_arm do`` ... ``end``）。后者深两格。写死四个空格会把顶层
    那个改歪 —— brew style 会报错，缩进不对的文件看着也别扭。
    """
    out = list(cask.lines)
    for index, line in enumerate(out):
        version = VERSION_RE.match(line)
        if version:
            out[index] = f'  version "{new_version}"'
    for index, sha in shas.items():
        indent = _indent_of(cask.lines[index])
        out[index] = f'{indent}sha256 "{sha}"'
    for index, url in urls.items():
        indent = _indent_of(cask.lines[index])
        out[index] = f'{indent}url "{url}"'
    return "\n".join(out)


# ---------------------------------------------------------------------- 主流程


def sync_one(cask: Cask, apply: bool) -> tuple[bool, str]:
    """更新一个 cask。返回（有没有改，说明）。"""
    release = latest_stable(cask.owner, cask.repo)
    if release is None:
        return False, f"{cask.name}: 上游没有正式版"

    tag = release.get("tag_name", "")
    new_version = tag[1:] if tag.startswith("v") else tag
    if not new_version:
        return False, f"{cask.name}: release 没有 tag"
    if release.get("draft") or release.get("prerelease"):
        # /releases/latest 本来就不给这两种，这是兜底。
        return False, f"{cask.name}: {tag} 不是正式版，跳过"

    if new_version == cask.version:
        return False, f"{cask.name}: 已经是最新（{cask.version}）"

    shas: dict[int, str] = {}
    urls: dict[int, str] = {}
    for slot in cask.slots:
        slot["old_version"] = cask.version
        asset = pick_asset(release, slot, new_version)
        if asset is None:
            return False, (
                f"{cask.name}: 找不到 {new_version} 的资产，跳过"
                f"（模板 {slot['template']}）"
            )
        if slot["sha_index"] is None:
            return False, f"{cask.name}: 有一个 url 找不到对应的 sha256"
        try:
            shas[slot["sha_index"]] = sha256_of_asset(
                release, asset, f"{cask.owner}/{cask.repo}"
            )
        except (urllib.error.URLError, urllib.error.HTTPError, LookupError) as exc:
            return False, f"{cask.name}: 下载 {asset} 失败（{exc}）"

        # **url 里保留 ``#{version}``。** 那是 cask 的活模板：以后再更新
        # 版本，url 自己就跟着变。写成写死的版本号就把这个性质弄丢了。
        # 只有资产名跟模板对不上时（上游改了文件命名）才换资产名那一段。
        template = slot["template"]
        template_asset = template.split("#{version}")[-1].split("/")[-1]
        if template_asset.replace("#{version}", new_version) == asset:
            # 资产名没变：模板原样留着。
            url = template
        else:
            # 资产名变了：只换最后那一个文件名，版本那段仍留模板。
            url = template.replace(template_asset, asset)
        urls[slot["index"]] = url

    text = rewrite(cask, new_version, shas, urls)
    if apply:
        cask.path.write_text(text, encoding="utf-8")

    return True, f"{cask.name}: {cask.version} → {new_version}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="只报告要改什么，不动文件",
    )
    parser.add_argument(
        "--cask",
        action="append",
        default=[],
        help="只处理这一个 cask（可以重复给）",
    )
    args = parser.parse_args()

    targets = CASKS
    if args.cask:
        wanted = set(args.cask)
        # 这里的 c 是 Path，不是 Cask：Path.name 是带后缀的文件名
        # （skycmedia.rb），Path.stem 才是 cask 的名字（skycmedia）。
        targets = [c for c in CASKS if c.stem in wanted]
        missing = wanted - {c.stem for c in CASKS}
        if missing:
            print(f"没有这些 cask：{', '.join(sorted(missing))}")
            return 1

    changed = 0
    problems = 0
    for path in targets:
        try:
            cask = Cask(path)
        except ValueError as exc:
            print(f"✗ {exc}")
            problems += 1
            continue
        try:
            did, message = sync_one(cask, apply=not args.check)
        except (RuntimeError, urllib.error.URLError) as exc:
            print(f"✗ {cask.name}: 连不上 GitHub（{exc}）")
            problems += 1
            continue
        if did:
            changed += 1
            print(f"{'会更新' if args.check else '已更新'}：{message}")
        else:
            print(f"· {message}")
    if args.check:
        print(f"\n检查完毕：{changed} 个 cask 需要更新（没有改文件）")
    else:
        print(f"\n更新完毕：{changed} 个 cask 变了")
    if problems:
        print(f"{problems} 个 cask 出问题，没动")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
