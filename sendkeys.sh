#!/bin/sh

SCP_CMD="scp -F /home/jez/.ssh/config"
SSH_CMD="ssh -F /home/jez/.ssh/config"

name=${1:?too few arguments}

usage () {
	echo "usage: sendkeys [server_name] [cmd] ..."
}


do_scp () {

${SCP_CMD} /home/jez/.ssh/.prv $name:/home/jez/.ssh/authorized_keys
${SCP_CMD} keys/ca.crt root@${name}:/etc/openvpn/
${SCP_CMD} keys/${name}.key root@${name}:/etc/openvpn/client.key
${SCP_CMD} keys/${name}.crt root@${name}:/etc/openvpn/client.crt
${SCP_CMD} client.conf root@${name}:/etc/openvpn/
${SSH_CMD} ${name} 'mkdir -m 700 -p /home/jez/.ssh'
}

gen_configs () {
	cd /home/jez/code/openssl/easy-rsa/1.0
	. ./vars
	./build-key ${1:?too few arguments to gen_configs}
}

if [ -z ${name} ]; then
	usage
	exit 64;
fi

shift
for cmd in $@
do
	case $cmd in
		generate)
			gen_configs $name;
			;;
		copy_configs)
			do_scp;
			;;
		*)
			printf "ERROR: unknown command \"%s\"\n" "${cmd}"
			usage;
			exit 64;
			;;
	esac

		
done

