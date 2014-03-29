#!/bin/sh -x -n
###############################################################################
# 
# Plan: 
# Arguments: [sudo user]
# root mode - installing packages
# user mode - setting ${HOME} up creating necessary files and extracting
#             shell configs
###############################################################################

fuckOS="";
FUCKSITE="http://capsel.org/~fred/fuck/"
#
fu_print () {
	echo "$@"
	
}

guess_os () {
	case "$(uname)" in
		"FreeBSD")
			fuckOS="FreeBSD";
			;;
		*[lL]inux*)
			fuckOS="Linux";
			;;
		*Darwin*)
			fuckOS="Darwin";
			;;
		*)
			fuckOS="Error $(uname) is an unknown OS";
			;;
	esac
	echo "=> Detected ${fuckOS}";
}

http_get () {
	dst=$1;shift;
	echo "Downloading ${1} to ${dst}";
	case "${fuckOS}" in
		"FreeBSD")
			if ! fetch -o "${dst}" "${1}"; then
				return 3;
			fi
			;;
		"Linux")
			if ! wget -q -O "${dst}" "${1}"; then
				return 3;
			fi
			;;
		"Darwin")
			if ! ftp  -o "${dst}" "${1}"; then
				return 3;
			fi
			;;
		*)
			echo "Unknown operating system \"${fuckOS}\"";
			return 32;
			;;
	esac
	return 0;
}

fuck_mkdir () {
	if [ -d "$1" ]; then
		echo "Directory \"$1\" already exists! Skipping" >> /tmp/fuck.log
		return;
	fi
	if ! mkdir -m 700 "$1"; then
		echo "Failed to create \"$1\"" >> /tmp/fuck.log
	fi
}


fuck_init () {
	#if ! mkdir ${fk_temporary}; then
	#	echo "Fuckshhh! Don't fuck.sh same OS twice!"
	#	exit 3;
	#fi

	guess_os;
	fuck_mkdir ~/bin;
	fuck_mkdir ~/code;
	fuck_mkdir ~/lib;
	fuck_mkdir ~/lib/zsh;
	fuck_mkdir ~/tmp;
	fuck_mkdir ~/.ssh;
	fuck_mkdir ~/.irssi;
}

fuck_root () {
	local fk_user="${1}";
	local fk_user_home="$(grep ${fk_user} /etc/passwd|cut -d ':' -f 6)"

	if [ -z "${fk_user}" ]; then
		echo "fuck_root(): Too few arguments";
		return 1;
	fi
	if [ ! -f "${fk_user_home}/.fucking_done" ]; then
		echo "fuck_root(): First You need to fuck.sh user's home directory";
		return 1;
	fi
	echo "=> Fucking root as ${fk_user}"
	install -o root -m 600 ${fk_user_home}/.vimrc ~/
	install -o root -m 600 ${fk_user_home}/.lynxrc ~/
	http_get ~/tmp/append_dot.bashrc "${fucksite}/append_dot.bashrc" 
	cat ~/tmp/append_dot.bashrc >> ~/.bashrc
}

########################################################################
### main
#
echo '===> Setting fuck.sh'
fuck_init;

case ${1} in
	"nohistory")
		ln -vsf /dev/null ~/.bash_history
		ln -vsf /dev/null ~/.mysql_history
		ln -vsf /dev/null ~/.ksh_history
		ln -vsf /dev/null ~/.sh_history
		;;
esac

if [ "${SHELL}" = "/bin/sh" ]; then
	echo "=> /bin/sh Detected!"
fi

if [ "$(id -u)" -eq "0" ]; then
	fuckuser="${1:-jez}";
	fuck_root "${fuckuser}";
	echo '===> Finished!';
	exit 0;
fi

http_get ~/.vimrc "${fucksite}/dot.vimrc"
http_get ~/.cshrc "${fucksite}/dot.cshrc"
http_get ~/.bashrc "${fucksite}/dot.bashrc"
http_get ~/.bash_logout "${fucksite}/dot.bash_logout"
http_get ~/.lynxrc "${fucksite}/dot.lynxrc"
http_get ~/.zshrc "${fucksite}/dot.zshrc"
http_get ~/ssh_key "${fucksite}/Jezssh.key"
cat ~/ssh_key >> ~/.ssh/authorized_keys

case ${fuckOS} in
	FreeBSD)
		http_get ~/.csh_aliases "${fucksite}/dot.csh_aliases.FreeBSD"
		http_get ~/.bash_aliases "${fucksite}/dot.bash_aliases.FreeBSD"
	;;
	*[Ll]inux*)
		http_get ~/.bash_aliases "${fucksite}/dot.bash_aliases.Linux"
	;;
	*Darwin*)
		http_get ~/.bash_aliases "${fucksite}/dot.bash_aliases.Darwin"
	;;
esac

date '+%s' >> ~/.fucking_done

echo '===> Finished!';

# self destructive code
rm -v fuck.sh
# end of fuck.sh
