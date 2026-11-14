cask "skycmedia" do
  version "3.25.1"

  on_arm do
    sha256 "959e628b752e50e1ab65ff75496d845be41a8f43715ee8f4fb2b2aeb1968ff21"

    url "https://github.com/Mofan2020/ncm/releases/download/v#{version}/SkycMedia-macOS-arm64.dmg"
  end
  on_intel do
    sha256 "a833a9d71f287bef1bb06bab810a7dafdc118b17bea77077f4ee1665115375d4"

    url "https://github.com/Mofan2020/ncm/releases/download/v#{version}/SkycMedia-macOS-x64.dmg"
  end

  name "SkycMedia"
  desc "Third-party client for Bilibili and NetEase Cloud Music"
  homepage "https://github.com/Mofan2020/ncm"

  livecheck do
    url "https://github.com/Mofan2020/ncm/releases.atom"
    regex(/SkycMedia\s+v?(\d+(?:\.\d+)+)/i)
    strategy :page_match
  end

  depends_on :macos

  app "SkycMedia.app"

  uninstall quit: "com.skyc8266.skycmedia"

  caveats <<~EOS
    Every release of SkycMedia on GitHub is currently a pre-release, so this
    cask tracks pre-releases. Expect rough edges between versions.

    The app is ad-hoc signed and not notarised. macOS may ask you to allow it
    in System Settings → Privacy & Security the first time you open it.
  EOS
end
