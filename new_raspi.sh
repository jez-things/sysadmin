#!/bin/sh -C
####################
#
######################################################
# VARIABLES:
##


PKG_LIST="vim lynx openvpn munin-node lsof tcpdump libmosquitto0 libmosquitto0-dev libmosquittopp0-dev mosquitto mosquitto-clients python-mosquitto syslog-ng tmux screen"
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
	my_print "msg" "-> Initialization of user ${1:?too few arguments}"
	if ! id jez > /dev/null 2>&1; then
		useradd -m jez
		passwd jez
	else
		my_print "User \"${DEFAULT_USER}\" already exists"
	fi
	mkdir -v -m 700 -p /home/jez/code
	cd /home/jez/code
	extr_urllist;
	for url in $(grep -v '^#.*' $URLLIST);
	do
		fetch_cmd "$url" |  tar  -xzvf - 

	done
	# git repositories:
	git clone git://git.drogon.net/wiringPi
	git clone https://github.com/jezjestem/digitalhoryzont.git
	git clone https://github.com/jezjestem/RaspberryPi.git
	git clone https://github.com/jezjestem/sysadmin.git
	my_print "Changing ownership to \"${DEFAULT_USER}\""
	chown -R ~jez/
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
			user_init "jez";
			;;
		*)
			usage;
			;;
	esac
done

