{ pkgs ? import <nixpkgs> {} }: pkgs.mkShell { packages = [(pkgs.python3.withPackages (p: [p.django p.pillow]))]; }
