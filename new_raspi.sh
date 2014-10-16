#!/bin/sh -C
####################
#
######################################################
# VARIABLES:
##


PKG_LIST="vim lynx openvpn munin-node lsof tcpdump libmosquitto0 libmosquitto0-dev libmosquittopp0-dev mosquitto mosquitto-clients python-mosquitto syslog-ng tmux screen python-dev python-serial python-daemon python-lockfile i2c-tools python-smbus rcs"
DEFAULT_USER="jez"
defcmds="packages configuration addones"
PROGNAME=$0
URLLIST=""
NOEXEC=0

dprint () {
	# XXX double check of condition considered hardful ;p
	[ "${DEBUG_MODE:-0}" -gt 0 ] && printf "DEBUG: %s\n" "$@"
	[ "${DEBUG_MODE:-0}" -gt 0 ] && logger  "${@}"
}

err_print () {
	printf "ERROR: %s\n" "${1:?too few arguments}"
	exit 3;
}

my_print () {
	ptype="${1:-msg}"
	mbuf="${2:-no message}"
	case ${ptype:?internal error} in
		msg)
			printf -- '-=> %s\n' "${mbuf}"
			;;
		hdr)
			printf '==============================>'
			printf -- '-=> %s\n' "${mbuf}"
			;;
		*)
			printf -- '-> %s\n' "${@}"
			return 0;
	esac
	return 0;
}


fetch_cmd () {
	url={$1:?$0 too few arguments}
	dprint "fetching ${url}"
	if [ "${NOEXEC:-0}" -gt 0 ]; then
		echo wget -q "${url}"
	else
		wget -q -O-  "${url}"
	fi

}

pkg_init () {
	for pkg in $PKG_LIST
	do
		if [ "${NOEXEC:-0}" -gt 0 ]; then
			echo apt-get install -y $pkg
		else
			apt-get install -y $pkg
		fi
	done

}

config_init () {
	if [ "$(id -u)" -ne 0 ]; then
		echo "need to be root"
		return 1;
	fi	
	#####################################################
	# syslog-ng remote logging feature
	#####################################################
	cat <<- END > /etc/syslog-ng/conf.d/netlog.conf
destination d_net { udp("192.168.0.217" port(514) log_fifo_size(65535)); };
log { source(s_src); destination(d_net); };
END
	#####################################################
	# openvpn config
	#####################################################

	cat <<- END > /etc/openvpn/client.conf
client
dev tun
proto udp
remote horyzont.bzzz.net 61194
;remote-random
resolv-retry infinite
nobind
;user nobody
;group nogroup
persist-key
persist-tun
;mute-replay-warnings
ca /etc/openvpn/ca.crt
cert /etc/openvpn/client.crt
key /etc/openvpn/client.key
ns-cert-type server
;tls-auth ta.key 1
;cipher x
comp-lzo
verb 3
status /var/run/openvpn.client.status 15

END

	return 0;
}

extr_urllist () {
	URLLIST=$(mktemp urllist.XXXXXXX)
	set +C
	cat <<- EOF > $URLLIST
	# $(date)
http://www.airspayce.com/mikem/bcm2835/bcm2835-1.36.tar.gz
EOF
	set -C
}

user_init () {
	new_user="${1:?user_init too few arguments}"
	my_print "msg" "-> Initialization of user ${1:?too few arguments}"
	if ! id "${new_user}" > /dev/null 2>&1; then
		useradd -m ${new_user}
		passwd ${new_user}
	else
		my_print "User \"${new_user}\" already exists"
		exit 3;
	fi
	mkdir -v -m 700 -p /home/${new_user}/code
	cd /home/${new_user}/code
	extr_urllist;
	for url in $(grep -v '^#.*' $URLLIST);
	do
		fetch_cmd "$url" |  tar  -xzvf - 

	done
	cd bcm2835-1.36/ && ./configure && make && make install && cd ..
	
	# git repositories:
	git clone git://git.drogon.net/wiringPi
	cd wiringPi && ./build && ./build install && cd ..
	git clone https://github.com/jezjestem/digitalhoryzont.git
	git clone https://github.com/jezjestem/RaspberryPi.git
	git clone https://github.com/jezjestem/sysadmin.git
	git clone git://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code.git
	cd Adafruit-Raspberry-Pi-Python-Code/Adafruit_DHT_Driver_Python &&  python setup.py build
	cd Adafruit-Raspberry-Pi-Python-Code/Adafruit_DHT_Driver_Python &&  python setup.py install
	cd ..
	my_print "Changing ownership to \"${new_user}\""
	chown -R "/home/${new_user}"
	my_print "Adding \"${new_user}\" to /etc/sudoers file"
	printf '%s ALL=(ALL) NOPASSWD: ALL\n' "${new_user}" >> /etc/sudoers
	my_print "Setting kernel modules:"
	printf "w1-gpio\nw1-therm\n\n" >> /etc/modules

}

usage () {
	echo "usage: ${PROGNAME} [packages|config|user]"
	exit 64;
}
####################
# main
######################################################

dprint $@ 
if [ ${#@} -le 0 ] ; then 
	echo 'too few arguments'
	usage;

fi

for cmd in $@
do
	case ${cmd} in
		packages)
			pkg_init;
			;;
		config)
			config_init;
			;;
		user)
			user_init "${DEFAULT_USER}";
			;;
		*)
			usage;
			;;
	esac
done

