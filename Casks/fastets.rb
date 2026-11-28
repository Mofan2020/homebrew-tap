# frozen_string_literal: true

cask "fastets" do
  version "1.0.11"

  on_arm do
    sha256 "ab966c628a5a590cbeb67914c2438ab7071b36bbacaa4bf74274ef8796f022e4"

    url "https://github.com/Mofan2020/FastETS/releases/download/v#{version}/FastETS-macOS-arm64.zip"
  end
  on_intel do
    sha256 "a333ddbe857b4b2c098e3c1368778959c7c789250e5fd525e1527c45371297e0"

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
