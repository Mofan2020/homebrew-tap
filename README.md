# Mofan2020 Tap

Skyc8266 的 Homebrew tap。

## 安装

```sh
brew install mofan2020/tap/deepsleep
```

或者先 tap 再装：

```sh
brew tap mofan2020/tap
brew install deepsleep
```

在 `Brewfile` 里：

```ruby
tap "mofan2020/tap"
brew "deepsleep"
```

## 收录的 cask

| cask | 说明 |
| --- | --- |
| `deepsleep` | macOS 睡眠与电源管理工具，原生 Swift，要求 macOS 26 以上 |

[Deep Sleep 项目主页](https://github.com/Mofan2020/DeepSleep)

## 签名说明

这些应用是 ad-hoc 签名，没有走 Apple 的公证流程。第一次打开时 macOS 可能拦截，
到「系统设置 → 隐私与安全性」点「仍要打开」即可。
