cask "skycmedia" do
  version "3.24.3"

  on_arm do
    sha256 "741b6171c3582ae9a11b490ee0af919f508da179a0deb695662edb14309c907b"

    url "https://github.com/Mofan2020/ncm/releases/download/v#{version}/SkycMedia-macOS-arm64.dmg"
  end
  on_intel do
    sha256 "c6899c39518d19b7d7f380df9387439406654ed4ac6081d2287a87f889bf71b1"

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
