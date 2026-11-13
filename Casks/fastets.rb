cask "fastets" do
  version "1.0.10"

  on_arm do
    sha256 "8f2473441a32f3e38c5aad896d08a611c5a95efd7aa814cd3791c8dabf404750"

    url "https://github.com/Mofan2020/FastETS/releases/download/v#{version}/FastETS-macOS-arm64.zip"
  end
  on_intel do
    sha256 "26cba5df8a6fd02f4d02d023f8a2b38360adb79f39f595d2d76e13e182731549"

    url "https://github.com/Mofan2020/FastETS/releases/download/v#{version}/FastETS-macOS-x64.zip"
  end

  name "FastETS"
  desc "Homework helper for ETS100 listening exercises"
  homepage "https://github.com/Mofan2020/FastETS"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on :macos

  app "FastETS.app"

  uninstall quit: "cc.fastets.app"

  caveats <<~EOS
    The app is ad-hoc signed and not notarised. macOS may ask you to allow it
    in System Settings → Privacy & Security the first time you open it.
  EOS
end
