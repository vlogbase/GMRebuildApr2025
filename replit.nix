{pkgs}: {
  deps = [
    pkgs.libyaml
    pkgs.zlib
    pkgs.xcodebuild
    pkgs.libev
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.jq
    pkgs.postgresql
    pkgs.openssl
  ];
}
