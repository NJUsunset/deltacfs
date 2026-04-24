#!/usr/bin/bash

if [ $# -eq 0 ]; then
    echo "ERROR: no input file for psgrn!"
    exit 1
elif [ $# -gt 1 ]; then
    echo "ERROR: more than one parameter are provided for psgrn!"
    exit 1
fi

input="$1"

if [[ "$input" == *.grn ]]; then
    echo $input | fomosto_psgrn2008a
else
    echo "ERROR: wrong input file type for psgrn!"
    exit 1
fi