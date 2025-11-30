{
  inputs.nixpkgs2009.url =github:galtys/nixpkgs/nixos-20.03pillow;
  outputs = { self, nixpkgs2009 }: 
    let
      pkgs9=nixpkgs2009.legacyPackages.x86_64-linux;

      migrated_pjb70_addons = pkgs9.stdenv.mkDerivation {
        name="migrated_pjb70_addons";
        src= ./addons;
        args = [ ./build.sh ];
        buildInputs = [pkgs9.coreutils];
        builder = "${pkgs9.bash}/bin/bash";
      };
      

      
    in  
      {
        packages.x86_64-linux.default=migrated_pjb70_addons;
      };

}
  
