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
| `skycmedia` | SkycMedia | B 站和网易云音乐的第三方客户端 |
| `superdownloadmanager` | SuperDownloadManager | 多线程下载管理器，仅 Apple Silicon |

FastETS 和 SkycMedia 会在 Apple Silicon 与 Intel 上各取对应的包；剩下三个上游只发了 Apple Silicon 版本，Intel 机器装不了。

## 预发布版本

HexoMan 最新的 v0.8.0 和 SkycMedia 现在所有版本，在 GitHub 上都是 pre-release。这两个 cask 跟着 pre-release 走，比正式版新，也可能有没修完的问题。`brew audit` 会因此报「是 pre-release」，这是预期内的。

## 签名说明

这些应用都是 ad-hoc 签名，没有走 Apple 的公证流程。第一次打开时 macOS 会拦截，到「系统设置 → 隐私与安全性」点「仍要打开」，或者：

```sh
xattr -dr com.apple.quarantine /Applications/HexoMan.app
```

SuperDownloadManager 自己可以装一个后台守护进程和 `sdm` 命令行工具，写的是 `~/Library/LaunchAgents/com.skyc8266.superdownloadmanager.daemon.plist` 和 `~/.local/bin/sdm`，`brew uninstall --zap` 会一起清掉。Deep Sleep 的「完全控制」会往 `/Library/PrivilegedHelperTools` 装一个 root 权限的助手，那个得它自己卸，命令在 cask 的 caveats 里。
