#!/bin/sh -C
####################
#
######################################################
# VARIABLES:
##


PKG_LIST="vim lynx openvpn munin-node lsof tcpdump libmosquitto0 libmosquitto0-dev libmosquittopp0-dev mosquitto mosquitto-clients python-mosquitto syslog-ng"

defcmds="packages configuration addones"
PROGNAME=$0
URLLIST=""
NOEXEC=1

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
	shift 1;
	mbuf="${1:?too few arguments}"
	case ${ptype:?internal error} in
		msg)
			printf "-=> %s\n"
			;;
		hdr)
			printf '==============================>'
			printf "-=> %s\n"
			;;
		*)
			err_print "$0 unknown print type"
			# NOTREACHED
			return 1;
	esac
	return 0;
}


fetch_cmd () {
	url={$1:?too few arguments}
	dprint "${url}"
	if [ "${NOEXEC:-0}" -gt 0 ]; then
		echo wget -q "${url}"
	else
		wget -q -O-  "${url}"
	fi

}

get_pkgs () {
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
	cat <<- EOF > $ulist
	# $(date)
http://www.airspayce.com/mikem/bcm2835/bcm2835-1.36.tar.gz
EOF
}

user_init () {
	echo "-> Initialization of user ${1:?too few arguments}"
	if ! id jez > /dev/null 2>&1; then
		useradd -m jez
		passwd jez
	fi
	mkdir -m 700 -p /home/jez/code
	cd /home/jez/code
	extr_urllist;
	for url in $(grep -v '^#.*' $URLLIST);
	do
		fetch_cmd "$url"

	done
	# git repositories:
	git clone git://git.drogon.net/wiringPi
	git clone https://github.com/jezjestem/digitalhoryzont.git
	git clone https://github.com/jezjestem/RaspberryPi.git
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
			user_init;
			;;
		*)
			usage;
			;;
	esac
done

