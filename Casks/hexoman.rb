# frozen_string_literal: true

cask "hexoman" do
  version "0.6.1"
  sha256 "8e67d3b4b764bd88205140b432d0362df69764ef90347cbef53b6bb6e7eeded1"

  url "https://github.com/Mofan2020/HexoMan/releases/download/v#{version}/HexoMan-#{version}-macos.zip"
  name "HexoMan"
  desc "Hexo blog manager for sites, posts, builds and Git"
  homepage "https://github.com/Mofan2020/HexoMan"

  livecheck do
    url :url
    strategy :github_latest
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
    This tap only ever installs a stable release. Newer versions of HexoMan
    are published as pre-releases on GitHub; install those from the release
    page if you want them.

    The version written inside the app comes from the upstream package and
    can lag behind the release number.

    The app is ad-hoc signed and not notarised. macOS may ask you to allow it
    in System Settings → Privacy & Security the first time you open it.

    HexoMan ships no runtime of its own: it calls the Node.js, npm and Git you
    already have installed.
  EOS
end
