cask "deepsleep" do
  version "1.8.1"
  sha256 "7dbd5d0e654c1f399bbdf4983f9b5c9203d92e873a1d9d979ad016ea2d9acfcc"

  url "https://github.com/Mofan2020/DeepSleep/releases/download/v#{version}/DeepSleep.zip"
  name "Deep Sleep"
  desc "Sleep and power manager"
  homepage "https://github.com/Mofan2020/DeepSleep"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on macos: :tahoe

  app "Deep Sleep.app"

  uninstall quit: "com.skyc8266.deepsleep"

  zap trash: [
    "~/Library/Application Support/com.skyc8266.deepsleep",
    "~/Library/Caches/com.skyc8266.deepsleep",
    "~/Library/LaunchAgents/com.skyc8266.deepsleep.plist",
    "~/Library/Logs/Deep Sleep",
    "~/Library/Preferences/com.skyc8266.deepsleep.plist",
    "~/Library/Saved Application State/com.skyc8266.deepsleep.savedState",
  ]

  caveats <<~EOS
    The app is ad-hoc signed. macOS may ask you to allow it in
    System Settings → Privacy & Security the first time you open it.

    "Full control" installs a privileged helper into
    /Library/PrivilegedHelperTools, owned by root, so `brew uninstall`
    cannot remove it without your password. Remove it from the app itself
    ("完全控制" → "停用并卸载"), or run:

      sudo '/Applications/Deep Sleep.app/Contents/Resources/uninstall-helper.sh'

    The same applies to the hosts editor whitelist under
    /Library/Application Support/com.skyc8266.deepsleep.
  EOS
end
