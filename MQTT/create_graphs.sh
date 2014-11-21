#!/bin/bash -e

graphs="temperature.png light.png humidity.png"
if ! ./read_statistics.py; then
	echo "failed to generate statistics!"
exit 0
fi
for g in $graphs
do
	echo "Installing $g"
	install -m 644 -o root -g www $g /var/www/statistics/$g
done	

echo "Created! "
