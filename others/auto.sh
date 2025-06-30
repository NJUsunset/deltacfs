#!/usr/bin/bash

echo "Script will use PSCMP/PSGRN to  calculate green funtion and deformation!"

read  -p "Calculate Green function?(yes/no/abort, default:no):" ifgrn

if [ -z "$ifgrn" ]; then
	echo "Using default option, skip Green function calculation."
elif [ "$ifgrn" = "yes" ]; then
	echo "Calculating Green function..."
	echo "psgrn08-wenchuan.inp" | /usr/local/bin/fomosto_psgrn2008a
elif [ "$ifgrn" = "no" ]; then
	echo "Skip Green function calculation."
elif [ "$ifgrn" = "abort" ]; then
	echo "Abort. Stopping script..."
	exit 0
else
	echo "Bad input. Stopping script..."
	exit 1
fi

read -p "Calculate deformation?(yes/no/abort, default:no):" ifcmp

if [ -z "$ifcmp" ]; then
	echo "Using default option. skip deformation calculation."
elif [ "$ifcmp" = "yes" ]; then
	echo "Calculating deformation..."
	echo "pscmp08-wenchuan.inp" | /usr/local/bin/fomosto_pscmp2008a
elif [ "$ifcmp" = "no" ]; then
	echo "Skip deformation calculation."
elif [ "$ifcmp" = "abort" ]; then
	echo "Abort. Stopping script..."
	exit 0
else
	echo "Bad input. Stopping script..."
	exit 1
fi

echo "Script work finished. Stopping script..."
