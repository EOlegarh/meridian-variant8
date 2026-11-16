{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.python3 pkgs.zlib ];
  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.zlib ];
}
