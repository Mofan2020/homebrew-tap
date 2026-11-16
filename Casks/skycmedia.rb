# frozen_string_literal: true

cask "skycmedia" do
  version "3.27.0"

  on_arm do
    sha256 "c446eba103dc8560e01b228e01e530eb5f70fa087303921b197e47036b41b031"

    url "https://github.com/Mofan2020/ncm/releases/download/v#{version}/SkycMedia-macOS-arm64.dmg"
  end
  on_intel do
    sha256 "b6b764e9c0959726805eaa20ac4a35cd9691fcc67cc2b1ba758617a18877154d"

    url "https://github.com/Mofan2020/ncm/releases/download/v#{version}/SkycMedia-macOS-x64.dmg"
  end

  name "SkycMedia"
  desc "NetEase Cloud Music client"
  homepage "https://github.com/Mofan2020/ncm"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on :macos

  app "SkycMedia.app"

  uninstall quit: "com.skyc8266.skycmedia"

  caveats <<~EOS
    This tap only ever installs a stable release. Every newer version of
    SkycMedia on GitHub is a pre-release; install those from the release
    page if you want them.

    The app is ad-hoc signed and not notarised. macOS may ask you to allow it
    in System Settings → Privacy & Security the first time you open it.
  EOS
end
