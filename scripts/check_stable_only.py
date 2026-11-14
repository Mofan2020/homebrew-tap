#!/usr/bin/env python3
"""这个 tap 只跟稳定版：每个 cask 指向的必须是**正式发布**的版本。

**为什么要有这个脚本。** 规则是「只允许更新到稳定版（latest），任何
pre-release 都不许进 tap」。规则只写在脑子里的话，迟早有一次手滑把
pre-release 的版本号和 sha256 填进去 —— 而 `brew install` 会照装不误，
用户拿到的是一个「pre-release 却被说成稳定」的包。

所以把规则变成一道闸门：读每个 cask 的版本号和仓库，查 GitHub 上那个
tag 是不是正式版；livecheck 的策略必须是 `github_latest`（它只认
`/releases/latest`，永远不会给出 pre-release）。

用法：
    python3 scripts/check_stable_only.py           # 需要能访问 api.github.com
    python3 scripts/check_stable_only.py --offline # 只做本地检查（不联网）

退出码 0 表示全过，1 表示有 cask 指向了 pre-release 或者写坏了。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASKS = sorted((ROOT / "Casks").glob("*.rb"))

#: livecheck 只允许这一种策略。它跟的是 /releases/latest —— GitHub 那边
#: 的 latest 不含 pre-release 和 draft，所以升级提示永远落在稳定版上。
ALLOWED_STRATEGY = ":github_latest"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.MULTILINE)
VERSION_RE = re.compile(r'^\s*version\s+"([^"]+)"', re.MULTILINE)
HOMEPAGE_RE = re.compile(r'^\s*homepage\s+"https://github\.com/([^/"]+)/([^/"]+)"', re.MULTILINE)
SHA_RE = re.compile(r'^\s*sha256\s+"([0-9a-fA-F]+)"', re.MULTILINE)
STRATEGY_RE = re.compile(r"^\s*strategy\s+(\S+)", re.MULTILINE)


def parse_cask(path: Path) -> dict:
    """从 cask 文件里读出要检查的几样东西。"""
    text = path.read_text(encoding="utf-8")
    versions = VERSION_RE.findall(text)
    homepages = HOMEPAGE_RE.findall(text)
    shas = SHA_RE.findall(text)
    strategies = STRATEGY_RE.findall(text)
    return {
        "path": path,
        "version": versions[0] if versions else "",
        "owner": homepages[0][0] if homepages else "",
        "repo": homepages[0][1] if homepages else "",
        "shas": shas,
        "strategies": strategies,
    }


def fetch_release(owner: str, repo: str, tag: str) -> dict:
    """问 GitHub 那个 tag 到底是什么性质的发布。

    **优先用 ``gh``。** 本机的 Python 不一定认得 HTTPS 中间人那张根证书
    （用 urllib 直接问 api.github.com 会报 certificate verify failed），
    而 ``gh`` 用的是另一套证书链，通的。CI 里同样有 ``gh``，token 从环境
    变量拿。没有 ``gh`` 就退回 urllib。
    """
    endpoint = f"repos/{owner}/{repo}/releases/tags/{tag}"
    if shutil.which("gh"):
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        raise RuntimeError(result.stderr.strip() or "gh api 失败")

    url = f"https://api.github.com/{endpoint}"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline",
        action="store_true",
        help="不联网，只做本地检查（版本号写法、sha256、livecheck 策略）",
    )
    args = parser.parse_args()

    problems: list[str] = []
    checked = 0

    for path in CASKS:
        info = parse_cask(path)
        name = path.stem
        if not info["version"]:
            problems.append(f"{name}: 文件里没有 version")
            continue
        if not info["owner"] or not info["repo"]:
            problems.append(f"{name}: 文件里没有指向 GitHub 仓库的 homepage")
            continue
        if not info["shas"]:
            problems.append(f"{name}: 文件里没有 sha256")
        for sha in info["shas"]:
            if not SHA256_RE.match(sha):
                problems.append(f"{name}: sha256 不是 64 位小写十六进制：{sha!r}")
        for strategy in info["strategies"]:
            if strategy != ALLOWED_STRATEGY:
                problems.append(
                    f"{name}: livecheck 策略是 {strategy}，只允许 {ALLOWED_STRATEGY}"
                    "（它只认正式版）"
                )
        if not info["strategies"]:
            problems.append(f"{name}: livecheck 没有写 strategy")

        if args.offline:
            continue

        tag = f"v{info['version']}"
        try:
            release = fetch_release(info["owner"], info["repo"], tag)
        except urllib.error.HTTPError as exc:
            problems.append(f"{name}: 查不到 {tag}（HTTP {exc.code}）")
            continue
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            problems.append(f"{name}: 连不上 GitHub：{exc}")
            continue

        checked += 1
        if release.get("draft"):
            problems.append(f"{name}: {tag} 是草稿，不能进 tap")
        if release.get("prerelease"):
            problems.append(
                f"{name}: {tag} 是 pre-release，tap 只跟稳定版 —— "
                "把它换成最新的正式版"
            )

    for line in problems:
        print(f"✗ {line}")
    if problems:
        print(f"\n{len(problems)} 处不对。tap 只允许指向稳定版（正式发布）。")
        return 1

    if args.offline:
        print(f"本地检查通过：{len(CASKS)} 个 cask")
    else:
        print(f"通过：{len(CASKS)} 个 cask，{checked} 个版本确认是正式发布")
    return 0


if __name__ == "__main__":
    sys.exit(main())
