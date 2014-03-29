#!/bin/sh


case $1 in
	update)
		for d in $(find . -type d -maxdepth 1 -not -name ".*")
		do
			cd $d
			git pull origin
			cd ..
		done
	;;
	
	sync)
		for d in $(find . -type d -maxdepth 1 -not -name ".*")
		do
			cd $d
			git push origin master
			cd ..
		done
	;;
	init)
		mkdir -m 700 -p ~/code ; cd ~/code

		git clone https://github.com/jezjestem/sysadmin.git
		git clone https://github.com/jezjestem/digitalhoryzont.git
	;;
	*)
		echo "usage: $(basename $0) [update|sync|init]"
		exit 64;
		# -.
	;;
esac

