#!/usr/bin/env python3
"""检查 cask 里的应用名跟上游打包出来的名字对不对得上。

**为什么要有这个脚本。** ``sync_releases.py`` 能改版本号和 sha256，但改不了
应用的名字：上游把 app 从 ``NeteaseMusicDownloader.app`` 改叫
``SkycMedia.app`` 的时候，cask 里的 ``app "..."`` 和 ``uninstall quit:`` 也
得跟着改。脚本猜不出来 —— 那个名字只有把 dmg 挂上才看得到。

所以这里做的是另一件事：**把对不上的地方指出来**，让人去改。

它怎么知道上游叫什么：把上游最新正式版的 macOS 资产下载下来，解包出
``.app`` 目录名，再跟 cask 里的 ``app "..."`` 比。

用法::

    python3 scripts/check_app_names.py            # 检查全部
    python3 scripts/check_app_names.py --offline  # 只看本地写法，不下载

退出码 0 表示都对得上，1 表示有对不上的。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASKS = sorted((ROOT / "Casks").glob("*.rb"))

APP_RE = re.compile(r'^\s*app\s+"([^"]+)"', re.MULTILINE)
NAME_RE = re.compile(r'^\s*name\s+"([^"]+)"', re.MULTILINE)
UNINSTALL_RE = re.compile(r'^\s*uninstall\s+quit:\s*"([^"]+)"', re.MULTILINE)
VERSION_RE = re.compile(r'^\s*version\s+"([^"]+)"', re.MULTILINE)
HOMEPAGE_RE = re.compile(
    r'^\s*homepage\s+"https://github\.com/([^/"]+)/([^/"]+)"', re.MULTILINE
)
URL_RE = re.compile(r'^\s*url\s+"([^"]+)"', re.MULTILINE)

#: 只有 macOS 的 cask 才需要查 app 名字。Windows-only 的跳过。
MACOS_RE = re.compile(r"depends_on.*:macos|depends_on macos")


def gh_json(endpoint: str) -> dict:
    """问 GitHub 要一份 JSON。

    **用 ``gh``，不用 urllib。** 本机的 Python 不认得 HTTPS 中间人那张根
    证书，urllib 直接问 api.github.com 会报 certificate verify failed。
    """
    if shutil.which("gh"):
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        raise RuntimeError(result.stderr.strip() or "gh api 失败")
    url = f"https://api.github.com/{endpoint}"
    request = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def download_asset(repo_full: str, asset_id: int, target: Path) -> None:
    """下一个 release 资产到文件。"""
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
            raise RuntimeError(result.stderr.decode("utf-8", "replace").strip())
        target.write_bytes(result.stdout)
        return
    raise RuntimeError("需要 gh 才能下载资产")


def app_name_in_zip(path: Path) -> str | None:
    """从 zip 里找出 ``.app`` 目录名。"""
    try:
        with zipfile.ZipFile(path) as archive:
            for entry in archive.namelist():
                parts = entry.split("/")
                if len(parts) > 1 and parts[0].endswith(".app"):
                    return parts[0]
    except zipfile.BadZipFile:
        return None
    return None


def app_name_in_dmg(path: Path) -> str | None:
    """从 dmg 里找出 ``.app`` 目录名。

    dmg 得挂上才看得到，所以这里真的挂一下再卸掉。
    """
    if not shutil.which("hdiutil"):
        return None
    with tempfile.TemporaryDirectory() as tmp:
        mount = Path(tmp) / "mnt"
        result = subprocess.run(
            ["hdiutil", "attach", "-nobrowse", "-readonly", "-quiet",
             str(path), "-mountpoint", str(mount)],
            capture_output=True,
            timeout=300,
        )
        try:
            if result.returncode != 0:
                return None
            for entry in sorted(mount.iterdir()):
                if entry.name.endswith(".app"):
                    return entry.name
            return None
        finally:
            subprocess.run(
                ["hdiutil", "detach", str(mount), "-quiet"],
                capture_output=True,
                timeout=120,
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline",
        action="store_true",
        help="只检查本地写法（不下载上游资产）",
    )
    args = parser.parse_args()

    problems: list[str] = []
    checked = 0

    for path in CASKS:
        text = path.read_text(encoding="utf-8")
        apps = APP_RE.findall(text)
        if not apps:
            problems.append(f"{path.stem}: cask 里没有 app")
            continue
        if not MACOS_RE.search(text):
            continue

        cask_app = apps[0]
        homepages = HOMEPAGE_RE.findall(text)
        if not homepages:
            continue
        owner, repo = homepages[0]

        if args.offline:
            print(f"· {path.stem}: app {cask_app}")
            continue

        try:
            release = gh_json(f"repos/{owner}/{repo}/releases/latest")
        except (RuntimeError, urllib.error.URLError) as exc:
            problems.append(f"{path.stem}: 查不到 {owner}/{repo}（{exc}）")
            continue

        assets = release.get("assets", [])
        # 找那个 macOS 资产：dmg 优先，其次 zip。
        mac_asset = None
        for wanted in (".dmg", ".zip"):
            for asset in assets:
                name = asset["name"].lower()
                if wanted in name and "windows" not in name and "sha256" not in name:
                    mac_asset = asset
                    break
            if mac_asset:
                break
        if not mac_asset:
            continue

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / mac_asset["name"]
            try:
                download_asset(f"{owner}/{repo}", mac_asset["id"], target)
            except (RuntimeError, OSError) as exc:
                problems.append(f"{path.stem}: 下载 {mac_asset['name']} 失败（{exc}）")
                continue
            if target.suffix == ".zip":
                upstream_app = app_name_in_zip(target)
            else:
                upstream_app = app_name_in_dmg(target)

        if not upstream_app:
            print(f"· {path.stem}: 没在 {mac_asset['name']} 里找到 .app，跳过")
            continue

        checked += 1
        if upstream_app != cask_app:
            problems.append(
                f"{path.stem}: cask 写的是 {cask_app}，"
                f"上游 {mac_asset['name']} 里是 {upstream_app}"
            )
        else:
            print(f"· {path.stem}: app {cask_app} 对得上")

    for line in problems:
        print(f"✗ {line}")
    if problems:
        print(f"\n{len(problems)} 处对不上。")
        return 1
    if args.offline:
        print(f"\n本地检查通过：{len(CASKS)} 个 cask")
    else:
        print(f"\n通过：{len(CASKS)} 个 cask，{checked} 个 app 名字确认对得上")
    return 0


if __name__ == "__main__":
    sys.exit(main())
