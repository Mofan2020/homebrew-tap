cask "deepsleep" do
  version "1.8.1"
  sha256 "7dbd5d0e654c1f399bbdf4983f9b5c9203d92e873a1d9d979ad016ea2d9acfcc"

  url "https://github.com/Mofan2020/DeepSleep/releases/download/v#{version}/DeepSleep.zip"
  name "Deep Sleep"
  desc "macOS sleep and power manager"
  homepage "https://github.com/Mofan2020/DeepSleep"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on macos: :tahoe

  app "Deep Sleep.app"

  uninstall launchctl: "com.skyc8266.deepsleep.helper",
            quit:      "com.skyc8266.deepsleep",
            delete:    [
              "/Library/PrivilegedHelperTools/com.skyc8266.deepsleep.helper",
              "/Library/LaunchDaemons/com.skyc8266.deepsleep.helper.plist",
              "/Library/Application Support/com.skyc8266.deepsleep",
            ]

  zap trash: [
    "~/Library/Application Support/com.skyc8266.deepsleep",
    "~/Library/Caches/com.skyc8266.deepsleep",
    "~/Library/Preferences/com.skyc8266.deepsleep.plist",
    "~/Library/Saved Application State/com.skyc8266.deepsleep.savedState",
    "~/Library/Logs/Deep Sleep",
    "~/Library/LaunchAgents/com.skyc8266.deepsleep.plist",
  ]

  caveats <<~EOS
    The app is ad-hoc signed. macOS may ask you to allow it in
    System Settings → Privacy & Security the first time you open it.

    "Full control" installs a privileged helper into
    /Library/PrivilegedHelperTools. Removing the app with `brew uninstall`
    removes the helper too; the app's own uninstaller does the same job.
  EOS
end
