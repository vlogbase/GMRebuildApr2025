{pkgs}: {
  deps = [
    pkgs.libev
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.jq
    pkgs.postgresql
    pkgs.openssl
  ];
}
