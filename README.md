# Mofan2020 Tap

Skyc8266 的 Homebrew tap，收 Mofan2020 名下几个 macOS 应用的 cask。

## 安装

```sh
brew install --cask mofan2020/tap/deepsleep
brew install --cask mofan2020/tap/fastets
brew install --cask mofan2020/tap/hexoman
brew install --cask mofan2020/tap/skycmedia
brew install --cask mofan2020/tap/superdownloadmanager
```

先 tap 再装也行：

```sh
brew tap mofan2020/tap
brew install --cask deepsleep
```

在 `Brewfile` 里：

```ruby
tap "mofan2020/tap"
cask "deepsleep"
```

## 收录的 cask

| cask | 应用 | 说明 |
| --- | --- | --- |
| `deepsleep` | Deep Sleep | 睡眠与电源管理，原生 Swift，要求 macOS 26 以上 |
| `fastets` | FastETS | 易听说（ETS100）作业助手，Apple Silicon 和 Intel 各有独立安装包 |
| `hexoman` | HexoMan | Hexo 博客管理：站点、文章、构建、配置、Git，要求 macOS 26 以上，仅 Apple Silicon |
| `skycmedia` | SkycMedia | 网易云音乐的第三方客户端 |
| `superdownloadmanager` | SuperDownloadManager | 多线程下载管理器，仅 Apple Silicon |

FastETS 和 SkycMedia 会在 Apple Silicon 与 Intel 上各取对应的包；剩下三个上游只发了 Apple Silicon 版本，Intel 机器装不了。

因为只跟稳定版，这里几个 cask 的版本号会比上游的最新版本旧不少 —— 上游发新版时先发 pre-release，正式版发布之后这个 tap 才会跟上去。

## 只跟稳定版

**这个 tap 里的每一个 cask 都只指向正式发布的版本，任何 pre-release 都不进 tap。**

上面几个应用在 GitHub 上的新版本多半是 pre-release（Deep Sleep 1.12.0 起、SkycMedia 全部新版本、Super Download Manager 2.2.6 起、HexoMan 0.7.0 起）。想装那些，去 release 页面手动下：

- <https://github.com/Mofan2020/DeepSleep/releases>
- <https://github.com/Mofan2020/ncm/releases>
- <https://github.com/Mofan2020/SuperDownloadManager/releases>
- <https://github.com/Mofan2020/HexoMan/releases>

这条规则由 `scripts/check_stable_only.py` 守着：它逐个查 cask 指向的版本在 GitHub 上是不是正式发布，pre-release 就报错；仓库的 CI 每次 push 都会跑它。想在本地跑：

```sh
python3 scripts/check_stable_only.py
```

## 自动跟版本

上游发了正式版之后，这个 tap 自己会跟上去：`scripts/sync_releases.py` 问
GitHub 每个项目的最新正式版（`/releases/latest` 那个端点本来就不给
draft 和 pre-release），下载资产现算 sha256，改写 cask 的版本号和 sha256。

每天跑一次，有变化就开一个 PR，不会直接推 main。改不动的它会跳过 ——
比如上游把应用改了名（`app "..."` 和 `uninstall quit:` 也得跟着改，脚本
猜不出来），那种情况由 `scripts/check_app_names.py` 报出来。

```sh
python3 scripts/sync_releases.py --check   # 只看要改什么，不动文件
```

应用名字对不对，由 `scripts/check_app_names.py` 查：它把上游最新正式版的
macOS 包下下来，解包出 `.app` 的名字，跟 cask 里写的比。CI 每次 push 都会
跑它。

## 签名说明

这些应用都是 ad-hoc 签名，没有走 Apple 的公证流程。第一次打开时 macOS 会拦截，到「系统设置 → 隐私与安全性」点「仍要打开」，或者：

```sh
xattr -dr com.apple.quarantine /Applications/HexoMan.app
```

SuperDownloadManager 自己可以装一个后台守护进程和 `sdm` 命令行工具，写的是 `~/Library/LaunchAgents/com.skyc8266.superdownloadmanager.daemon.plist` 和 `~/.local/bin/sdm`，`brew uninstall --zap` 会一起清掉。Deep Sleep 的「完全控制」会往 `/Library/PrivilegedHelperTools` 装一个 root 权限的助手，那个得它自己卸，命令在 cask 的 caveats 里。
