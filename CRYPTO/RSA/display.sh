#!/bin/bash
file="parameters"
if [ ! -e $file ]; then
	echo "Key are not generated"
	echo "Select 1st option first (1,g,G) !!!"
else
	p=$(cat parameters | cut -d: -f1)
	q=$(cat parameters | cut -d: -f2)
	n=$(cat parameters | cut -d: -f3)
	phi=$(cat parameters | cut -d: -f4)
	e=$(cat parameters | cut -d: -f5)
	d=$(cat parameters | cut -d: -f6)
	echo "p=$p  q=$q  n=$n  phi=$phi"
        echo "(e,n)=($e,$n)  (d,n)=($d,$n)"
fi
