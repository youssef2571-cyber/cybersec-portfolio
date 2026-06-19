#!/bin/bash
#Function to check whether number is prime 
prime() {
    n=$1
    if [ $n -le 1 ]; then
        return 1  # faux
    fi
    if [ $n -le 3 ]; then
        return 0  # vrai
    fi
    i=2
    while [ $((i * i)) -le $n ]; do
        if [ $((n % i)) -eq 0 ] ; then
            return 1
        fi
        i=$((i + 1))
    done
    return 0  # prime number
}
#Function to calculate pgcd  
pgcd() {
    a=$1
    b=$2

    while [ "$b" -ne 0 ]; do
        r=$((a % b))
        a=$b
        b=$r
    done

    echo "$a"
}
#Function to calculate a number modular inverse
mod_inv() {
    r=$1; m=$2
    a=$m; b=$r; c=1; d=0
    while [ $b -ne 1 ]; do
	a1=$b 
	b1=$((a%b))
	c1=$(( (d-c*(a/b)) % m + m))
	d1=$c
	a=$a1; b=$b1; c=$c1; d=$d1
    done
    echo "$c"
}

#p,q generation
	 p=0;q=0
	while  ! prime $p; do
	  p=$(($RANDOM % 99 + 2))
	done
	while  ! prime $q; do
	  q=$(($RANDOM % 99 + 2))
	done
((n=p*q)); (( phi=(p-1)*(q-1) ))
echo p=$p q=$q
echo n=$n phi=$phi

# Public Key (e,n)  calculation
for e in $(seq 2 $((phi-2)) )
do
        if [ $(pgcd $e $phi) -ne 1 ]; then
	    ((e=e+1))
	else
	    break
	fi
done
echo "Public Key: (e,n)=($e,$n)"
# Private Key (d,n)  calculation
 priv=$(mod_inv $e $phi)
 echo "Private Key: (d,n)=($priv,$n)"
#Store values in a new file named parameters
 echo $p:$q:$n:$phi:$e:$priv > parameters 
