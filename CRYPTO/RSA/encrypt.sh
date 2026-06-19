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

# read RSA parameters
file="parameters"
if [ ! -e $file ]; then
	echo "Key are not generated"
	echo "Select 1st option first (1,g,G) !!!"
	exit
fi
  n=$(cat parameters | cut -d: -f3)
  e=$(cat parameters | cut -d: -f5)
  echo "Pub. key : (e,n)=($e,$n)"
  read -p "Message (number) to encrypt M = " M

# Check M
  if [ $M -ge $n ]; then
      echo "Error : M should be < n !!!"
      exit 1
  fi

# Encryption
  C=$(mod_pow $M $e $n)
echo "Cipher text : C = $C"
