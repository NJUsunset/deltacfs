#!/usr/bin/bash

if [ $# -eq 0 ]; then
    echo "ERROR: no input file for pscmp!"
    exit 1
elif [ $# -gt 1 ]; then
    echo "ERROR: more than one parameter are provided for pscmp!"
    exit 1
fi

input="$1"

if [[ "$input" == *.cmp ]]; then
    echo $input | /usr/local/bin/fomosto_pscmp2008a
else
    echo "ERROR: wrong input file type for pscmp!"
    exit 1
fi