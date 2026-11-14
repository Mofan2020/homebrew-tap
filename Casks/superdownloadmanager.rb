cask "superdownloadmanager" do
  version "2.3.1"
  sha256 "872e4cbb3548575ead084b9a8fe2a3e3a3d739589db66d527e505e77303526b7"

  url "https://github.com/Mofan2020/SuperDownloadManager/releases/download/v#{version}/SuperDownloadManager-macOS.zip"
  name "SuperDownloadManager"
  desc "Multi-threaded download manager"
  homepage "https://github.com/Mofan2020/SuperDownloadManager"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on arch: :arm64
  depends_on :macos

  app "SuperDownloadManager.app"

  uninstall launchctl: "com.skyc8266.superdownloadmanager.daemon",
            quit:      "com.skyc8266.superdownloadmanager"

  zap trash: [
    "~/.local/bin/sdm",
    "~/Library/LaunchAgents/com.skyc8266.superdownloadmanager.daemon.plist",
    "~/Library/Preferences/com.skyc8266.superdownloadmanager.plist",
    "~/Library/Saved Application State/com.skyc8266.superdownloadmanager.savedState",
  ]

  caveats <<~EOS
    The app is ad-hoc signed and not notarised. macOS may ask you to allow it
    in System Settings → Privacy & Security the first time you open it.

    The macOS build is Apple Silicon only. There is no Intel build upstream.

    The app can install a background daemon and a `sdm` command-line tool
    itself. That writes:

      ~/Library/LaunchAgents/com.skyc8266.superdownloadmanager.daemon.plist
      ~/.local/bin/sdm

    Both are removed by `brew uninstall --zap`, or on their own by running:

      '/Applications/SuperDownloadManager.app/Contents/Resources/uninstall.sh'
  EOS
end
