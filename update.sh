#!/bin/sh

for d in $(find . -type d -maxdepth 1 -not -name ".*")
do
	cd $d
	git pull origin
	cd ..
done
