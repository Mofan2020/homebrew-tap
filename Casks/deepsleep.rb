# frozen_string_literal: true

cask "deepsleep" do
  version "1.13.0"
  sha256 "2e959755730d00a08fb24a21c22e21c75c783613ae58c86f2204c91788f1619d"

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
    This tap only ever installs a stable release. Newer versions of Deep
    Sleep are published as pre-releases on GitHub; install those from the
    release page if you want them.

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
