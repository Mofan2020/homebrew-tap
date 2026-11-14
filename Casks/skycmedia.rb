# frozen_string_literal: true

cask "skycmedia" do
  version "3.5.4"

  on_arm do
    sha256 "d3a912da975c4b1672ea6fc4f00994e922c10eb7d201b312f74c4cafa6b55ccd"

    url "https://github.com/Mofan2020/ncm/releases/download/v#{version}/NeteaseMusicDownloader-macOS-arm64.dmg"
  end
  on_intel do
    sha256 "eb3ca7f5d376f8d51e152db12c0cb116fe62edf0c61b938e9151cc56817afb49"

    url "https://github.com/Mofan2020/ncm/releases/download/v#{version}/NeteaseMusicDownloader-macOS-x64.dmg"
  end

  name "NeteaseMusicDownloader"
  desc "NetEase Cloud Music client"
  homepage "https://github.com/Mofan2020/ncm"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on :macos

  app "NeteaseMusicDownloader.app"

  uninstall quit: "com.skyc8266.neteasemusicdownloader"

  caveats <<~EOS
    This tap only ever installs a stable release. Every newer version of
    SkycMedia on GitHub is a pre-release; install those from the release
    page if you want them.

    The app is ad-hoc signed and not notarised. macOS may ask you to allow it
    in System Settings → Privacy & Security the first time you open it.
  EOS
end
