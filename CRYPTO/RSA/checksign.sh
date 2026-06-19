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
e=$(cat parameters| cut -d: -f5)

echo -n "Signature S to Check:  "
read S
echo -n "Signed Message:  "
read M1
#Check S
M=$(mod_pow $S $e $n)

if [ $M -eq $M1 ]; then
     echo "La signature est Valide ($M,$S)"
else
     echo "La signature NON Valide!!!"
fi


