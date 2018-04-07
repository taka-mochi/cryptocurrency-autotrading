#!/bin/sh

span=$1

while [ true ] ; do
    idx=0
    for symbol in ${@}; do
	if [ $idx -ne 0 ] ; then
	    echo $symbol
	    wget "https://api.binance.com/api/v1/depth?symbol=${symbol}&limit=10" -O - >> depth_data/depth_${symbol}.txt
	    echo "" >> depth_data/depth_${symbol}.txt
	fi
	idx=$(expr $idx + 1)
    done
    echo "wait ${span}m"
    sleep ${span}m
done
