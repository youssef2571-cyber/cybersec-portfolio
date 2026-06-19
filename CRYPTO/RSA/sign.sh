#!/bin/bash
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
    
    
file="parameters"
if [ ! -e $file ]; then
        echo "Key are not generated"
        echo "Select 1st option first (1,g,G) !!!"
        exit
fi
n=$(cat parameters| cut -d: -f3)
d=$(cat parameters| cut -d: -f6)

echo -n "Message M to sign:  "
read M
# Check M
  if [ $M -ge $n ]; then
      echo "Error : M should be < n !!!"
      exit 1
  fi
#Sign M
S=$(mod_pow $M $d $n)
echo "La signature de $M est ($M,$S)"
