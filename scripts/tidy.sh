#!/bin/bash

F="$1"
[ -z "$1" ] && echo "Usage: $0 <file>.html" && exit 1

B=`basename "$F" .html`

tidy "$F" | sed -n '/\[\[new Date/,/\]\],/p' | head -1 | sed 's/.*\[\[//;s/\]\].*//' | sed 's/\],/\]\n/g' | sed 's/\[*new Date(\"\([^"]*\)")/\1/;s/\]//' | sed -n '/^2010\/07\/17/,$p' | tee "$B".csv
