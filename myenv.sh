#!/bin/sh

aur_make () {
	chmod 755 /root/bin/mk.sh
	
	su  jez --session-command="/home/jez//bin/mk.sh ${1:?}"
}

init_base () {
	 pacstrap /mnt/new base base-devel vim syslinux openssh
}


#pacman --noconfirm -S git aircrack-ng svn screen python2 samba  mkinitcpio-nfs-utils tmux gptfdisk gparted tcpdump vsftpd ntfs-3g  lm_sensors smartmontools python2-setuptools pciutils nfs-utils moc munin-node munin nginx minicom lsof lynx wget alsa-firmware alsa-utils alsa-tools apg gnupg 

sleep 1
	

#pacman --noconfirm -S python2-pyserial python2-lockfile

#pacman --noconfirm -S sysstat usbutils unzip unrar rfkill kismet figlet rcs  syslog-ng motion 

aur_make 'https://aur.archlinux.org/packages/ar/arduino-mk/arduino-mk.tar.gz'
aur_make 'https://aur.archlinux.org/packages/ks/ksh/ksh.tar.gz'
aur_make 'https://aur.archlinux.org/packages/py/python2-daemon/python2-daemon.tar.gz'
aur_make 'https://aur.archlinux.org/packages/py/python2-glob2-git/python2-glob2-git.tar.gz'

aur_make 'https://aur.archlinux.org/packages/ar/arduino/arduino.tar.gz'


aur_make 'https://aur.archlinux.org/packages/in/ino-git/ino-git.tar.gz'

aur_make 'https://aur.archlinux.org/packages/mo/mosquitto/mosquitto.tar.gz'
