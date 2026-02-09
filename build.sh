#export PATH="$coreutils/bin"
set -e
unset PATH
for p in $buildInputs; do
    export PATH=$p/bin${PATH:+:}$PATH
done
mkdir $out
cp -rf $src $out/addons
