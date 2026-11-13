cask "hexoman" do
  version "0.8.0"
  sha256 "7076bd2b2d11e703eca938dd7f159e00eff7260604e349eac4e1f8ef5a58f78c"

  url "https://github.com/Mofan2020/HexoMan/releases/download/v#{version}/HexoMan-#{version}-macos.zip"
  name "HexoMan"
  desc "Hexo blog manager for sites, posts, builds and Git"
  homepage "https://github.com/Mofan2020/HexoMan"

  livecheck do
    url "https://github.com/Mofan2020/HexoMan/releases.atom"
    regex(/HexoMan\s+v?(\d+(?:\.\d+)+)/i)
    strategy :page_match
  end

  depends_on arch: :arm64
  depends_on macos: :tahoe

  app "HexoMan.app"

  uninstall quit: "com.skyc8266.hexoman"

  zap trash: [
    "~/Library/Application Support/HexoMan",
    "~/Library/Caches/com.skyc8266.hexoman",
    "~/Library/Preferences/com.skyc8266.hexoman.plist",
    "~/Library/Saved Application State/com.skyc8266.hexoman.savedState",
  ]

  caveats <<~EOS
    v0.8.0 is published on GitHub as a pre-release; the newest non-pre-release
    there is v0.6.1. This cask tracks the pre-release line on purpose.

    The app is ad-hoc signed and not notarised. macOS may ask you to allow it
    in System Settings → Privacy & Security the first time you open it.

    HexoMan ships no runtime of its own: it calls the Node.js, npm and Git you
    already have installed.
  EOS
end
