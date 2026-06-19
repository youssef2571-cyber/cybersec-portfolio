#!/bin/bash
# Modular power function
mod_pow() {
    base=$1
    pow=$2
    mod=$3

    result=1
    base=$((base % mod))

    while [ $pow -gt 0 ]; do
        if [ $((pow % 2)) -eq 1 ]; then
            result=$(( (result * base) % mod ))
        fi
        pow=$((pow / 2))
        base=$(( (base * base) % mod ))
    done

    echo $result
}

# Read RSA parameters
file="parameters"
if [ ! -e $file ]; then
	echo "Key are not generated"
	echo "Select 1st option first (1,g,G) !!!"
	exit
fi
  n=$(cat parameters | cut -d: -f3)
  d=$(cat parameters | cut -d: -f6)
  echo "Priv. key : (d,n)=($d,$n)"
  read -p "Message (number) to decrypt C = " C

# Decryption
  M=$(mod_pow $C $d $n)
echo "Plain Text : M = $M"
