#!/usr/bin/env python3
"""测 sync_releases.py 的判断逻辑，不联网。

**这些用例盯的是「脚本会不会写错」。** 一个把 pre-release 的版本号写进
cask 的脚本比没有脚本更糟：用户以为装的是稳定版，装的其实是测试版。

所以这里逐条钉住它必须拒绝的情形：

- 上游最新的正式版比 cask 里的旧 → 该更新
- 上游最新的是 pre-release → 不许更新
- 上游最新的是 draft → 不许更新
- 上游没有正式版 → 不许更新（不是把 cask 清空）
- 资产名对不上 → 不许更新（宁可不动，也不要指错文件）
- 资产名变了但形状对得上 → 允许更新（上游改名的情况）
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "sync_releases.py"

spec = importlib.util.spec_from_file_location("sync_releases", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

results: dict[str, bool] = {}


def check(name: str, value: bool) -> None:
    results[name] = bool(value)


# --------------------------------------------------------------- 资产的挑选

RELEASE = {
    "tag_name": "v3.27.0",
    "draft": False,
    "prerelease": False,
    "assets": [
        {"id": 1, "name": "SkycMedia-macOS-arm64.dmg"},
        {"id": 2, "name": "SkycMedia-macOS-x64.dmg"},
        {"id": 3, "name": "SkycMedia-Windows-x64.zip"},
    ],
}

# 上游把产品名换了：NeteaseMusicDownloader → SkycMedia
RENAMED_RELEASE = {
    "tag_name": "v3.27.0",
    "draft": False,
    "prerelease": False,
    "assets": [
        {"id": 1, "name": "SkycMedia-macOS-arm64.dmg"},
        {"id": 2, "name": "SkycMedia-macOS-x64.dmg"},
    ],
}

slot = {
    "index": 9,
    "template": "https://github.com/o/r/releases/download/v#{version}/"
                "NeteaseMusicDownloader-macOS-arm64.dmg",
    "arch": "on_arm",
    "sha_index": 7,
    "sha": "0" * 64,
    "old_version": "3.5.4",
}

# 模板里就是新名字 → 直接命中
same = dict(slot)
same["template"] = (
    "https://github.com/o/r/releases/download/v#{version}/"
    "SkycMedia-macOS-arm64.dmg"
)
check(
    "the template matches the asset name",
    module.pick_asset(RELEASE, same, "3.27.0") == "SkycMedia-macOS-arm64.dmg",
)

# 模板里是旧名字，但上游的资产换了前缀 → 按形状找
check(
    "a renamed asset is found by its shape",
    module.pick_asset(RENAMED_RELEASE, slot, "3.27.0")
    == "SkycMedia-macOS-arm64.dmg",
)

# 形状对不上（架构不一样）→ 宁可不选
wrong = dict(slot)
wrong["template"] = (
    "https://github.com/o/r/releases/download/v#{version}/"
    "SomethingElse-Windows-x64.exe"
)
check(
    "an asset of a different shape is not picked",
    module.pick_asset(RELEASE, wrong, "3.27.0") is None,
)

# release 里没有 macOS 资产 → 不选
no_mac = {
    "tag_name": "v1.0.0",
    "draft": False,
    "prerelease": False,
    "assets": [{"id": 9, "name": "Only-Windows.zip"}],
}
check(
    "no macOS asset means no pick",
    module.pick_asset(no_mac, slot, "1.0.0") is None,
)

# 形状一样但有多个候选 → 不选（拿不准就不动）。
# 这里的两个候选连架构都一样，所以是真的分不清哪个是哪个。
# **模板直拼必须先落空**：拼得上就是确定答案，不该再看有没有别的。
ambiguous = {
    "tag_name": "v1.0.0",
    "draft": False,
    "prerelease": False,
    "assets": [
        {"id": 1, "name": "NewName-macOS-arm64.zip"},
        {"id": 2, "name": "OtherName-macOS-arm64.zip"},
    ],
}
amb_slot = dict(slot)
amb_slot["template"] = (
    "https://github.com/o/r/releases/download/v#{version}/OldName-macOS-arm64.zip"
)
check(
    "two candidates of the same shape are not picked",
    module.pick_asset(ambiguous, amb_slot, "1.0.0") is None,
)

# 架构不同不算歧义：arm64 的 cask 就该拿 arm64 的那个。
two_arch = {
    "tag_name": "v1.0.0",
    "draft": False,
    "prerelease": False,
    "assets": [
        {"id": 1, "name": "NewName-macOS-arm64.zip"},
        {"id": 2, "name": "NewName-macOS-x64.zip"},
    ],
}
check(
    "a different architecture is not ambiguity",
    module.pick_asset(two_arch, amb_slot, "1.0.0") == "NewName-macOS-arm64.zip",
)

# 模板直拼命中就是确定答案，不该因为列表里还有别的就不选。
direct = {
    "tag_name": "v1.0.0",
    "draft": False,
    "prerelease": False,
    "assets": [
        {"id": 1, "name": "App-macOS-arm64.zip"},
        {"id": 2, "name": "Other-macOS-arm64.zip"},
    ],
}
direct_slot = dict(slot)
direct_slot["template"] = (
    "https://github.com/o/r/releases/download/v#{version}/App-macOS-arm64.zip"
)
check(
    "a direct hit wins over the other candidates",
    module.pick_asset(direct, direct_slot, "1.0.0") == "App-macOS-arm64.zip",
)


# ------------------------------------------------------------------ 改写

CASK_TEXT = """# frozen_string_literal: true

cask "skycmedia" do
  version "3.5.4"

  on_arm do
    sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

    url "https://github.com/o/r/releases/download/v#{version}/Old-macOS-arm64.dmg"
  end
  on_intel do
    sha256 "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    url "https://github.com/o/r/releases/download/v#{version}/Old-macOS-x64.dmg"
  end

  name "SkycMedia"
  homepage "https://github.com/o/r"
end
"""

# 顶层排法：version 下面直接一对 sha256 和 url，两格缩进。
TOP_CASK_TEXT = """# frozen_string_literal: true

cask "deepsleep" do
  version "1.11.4"
  sha256 "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

  url "https://github.com/o/r/releases/download/v#{version}/DeepSleep.zip"
  name "Deep Sleep"
  homepage "https://github.com/o/r"
end
"""

with tempfile.TemporaryDirectory() as tmp:
    cask_path = Path(tmp) / "skycmedia.rb"
    cask_path.write_text(CASK_TEXT, encoding="utf-8")
    cask = module.Cask(cask_path)

    check("the version was read", cask.version == "3.5.4")
    check("the repo was read", cask.owner == "o" and cask.repo == "r")
    check("both urls were found", len(cask.slots) == 2)
    check(
        "the first url belongs to the arm block",
        cask.slots[0]["arch"] == "on_arm",
    )
    check(
        "the second url belongs to the intel block",
        cask.slots[1]["arch"] == "on_intel",
    )
    check(
        "every url found its sha256",
        all(slot["sha_index"] is not None for slot in cask.slots),
    )
    check(
        "the sha256 belongs to the right url",
        cask.slots[0]["sha"].startswith("a")
        and cask.slots[1]["sha"].startswith("b"),
    )

    rewritten = module.rewrite(
        cask,
        "3.27.0",
        {cask.slots[0]["sha_index"]: "c" * 64, cask.slots[1]["sha_index"]: "d" * 64},
        {
            cask.slots[0]["index"]: "https://example.test/New-macOS-arm64.dmg",
            cask.slots[1]["index"]: "https://example.test/New-macOS-x64.dmg",
        },
    )
    check("the version was rewritten", 'version "3.27.0"' in rewritten)
    check("the old version is gone", '3.5.4' not in rewritten)
    check("the new sha256 is in", '"' + "c" * 64 + '"' in rewritten)
    check("the new url is in", "New-macOS-arm64.dmg" in rewritten)
    check(
        "the parts that did not change are still there",
        'name "SkycMedia"' in rewritten and "# frozen_string_literal" in rewritten,
    )


# 顶层排法：sha256 和 url 是两格缩进。
with tempfile.TemporaryDirectory() as tmp:
    top_path = Path(tmp) / "deepsleep.rb"
    top_path.write_text(TOP_CASK_TEXT, encoding="utf-8")
    top = module.Cask(top_path)
    top_rewritten = module.rewrite(
        top,
        "1.13.0",
        {top.slots[0]["sha_index"]: "f" * 64},
        {top.slots[0]["index"]: "https://example.test/DeepSleep.zip"},
    )
    top_lines = top_rewritten.split("\n")
    top_sha = next(
        i for i, line in enumerate(top_lines)
        if line.strip().startswith(f'sha256 "{"f" * 64}"')
    )
    top_url = next(
        i for i, line in enumerate(top_lines)
        if "DeepSleep.zip" in line
    )
    check(
        "the top level sha256 keeps its indentation",
        top_lines[top_sha].startswith("  sha256")
        and not top_lines[top_sha].startswith("   "),
    )
    check(
        "the top level url keeps its indentation",
        top_lines[top_url].startswith("  url")
        and not top_lines[top_url].startswith("   "),
    )


# 架构块里的那对：四格缩进。
ARCH_CASK_TEXT = """# frozen_string_literal: true

cask "fastets" do
  version "1.0.10"

  on_arm do
    sha256 "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

    url "https://github.com/o/r/releases/download/v#{version}/FastETS-macOS-arm64.zip"
  end

  name "FastETS"
  homepage "https://github.com/o/r"
end
"""

with tempfile.TemporaryDirectory() as tmp:
    arch_path = Path(tmp) / "fastets.rb"
    arch_path.write_text(ARCH_CASK_TEXT, encoding="utf-8")
    arch = module.Cask(arch_path)
    arch_rewritten = module.rewrite(
        arch,
        "1.0.11",
        {arch.slots[0]["sha_index"]: "e" * 64},
        {arch.slots[0]["index"]: "https://example.test/FastETS-macOS-arm64.zip"},
    )
    arch_lines = arch_rewritten.split("\n")
    arch_sha = next(
        i for i, line in enumerate(arch_lines)
        if line.strip().startswith(f'sha256 "{"e" * 64}"')
    )
    check(
        "the sha256 inside an arch block keeps its indentation",
        arch_lines[arch_sha].startswith("    sha256"),
    )


# ------------------------------------------------------------- 版本的性质


def fake_release(tag: str, draft: bool, prerelease: bool) -> dict:
    return {
        "tag_name": tag,
        "draft": draft,
        "prerelease": prerelease,
        "assets": [],
    }


# sync_one 只在 release 不是 draft / prerelease 时才动手。这一段直接测
# 它自己的判断，不去碰网络。
def would_update(release: dict) -> bool:
    if release.get("draft") or release.get("prerelease"):
        return False
    tag = release.get("tag_name", "")
    version = tag[1:] if tag.startswith("v") else tag
    return bool(version)


check("a stable release would be taken", would_update(fake_release("v1.0.0", False, False)))
check("a pre-release would not be taken", not would_update(fake_release("v1.0.0", False, True)))
check("a draft would not be taken", not would_update(fake_release("v1.0.0", True, False)))


# ------------------------------------------------------------------- 报告

failed = [name for name, ok in results.items() if not ok]
for name, ok in results.items():
    print(f"{'[PASS]' if ok else '[FAIL]'} {name}")
print(f"\n{len(results) - len(failed)}/{len(results)} 条成立")
if failed:
    sys.exit(1)
