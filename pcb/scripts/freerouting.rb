class Freerouting < Formula
  desc "PCB signal autorouter, pinned for the TrueSkate carrier review"
  homepage "https://github.com/freerouting/freerouting"
  url "https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar"
  sha256 "f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7"
  license "GPL-3.0-or-later"
  depends_on "openjdk"

  def install
    libexec.install "freerouting-2.5.0.jar"
    (bin/"freerouting").write <<~EOS
      #!/bin/sh
      exec "#{Formula["openjdk"].opt_bin}/java" -jar "#{libexec}/freerouting-2.5.0.jar" "$@"
    EOS
  end
end
