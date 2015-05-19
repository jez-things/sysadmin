
# ~/.bashrc: executed by bash(1) for non-login shells.

# If not running interactively, don't do anything
[ -z "$PS1" ] && return

# don't put duplicate lines in the history. See bash(1) for more options
# ... or force ignoredups and ignorespace
#HISTCONTROL=ignoredups:ignorespace

# append to the history file, don't overwrite it
#shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=5000
HISTFILESIZE=0

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
#shopt -s checkwinsize



# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
#force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

bash_prompt () {
	echo -n "rudy "
}

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    #PROMPT_COMMAND="/bin/ls";
    PS1="`hostname` "
    ;;
*)
    ;;
esac
export PS1='\h \w (\j)\$ '

# some more ls aliases
alias ll='ls -alF'
alias la='ls -AF'
alias ls='ls -CF'
alias c='tput clear'
alias x='startxfce4'
alias repo="cd /home/jez/code/repos/sysadmin/MQTT"
alias j='jobs -l'
alias pstree='pstree -A -l -p -a '
set -o vi

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

if [ -n "${DISPLAY}" ]; then
	#cd ~/Desktop
	echo 'Desktop'
fi
# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
    . /etc/bash_completion
fi

auth_all_ssh_keys () {
	ssh-add ~/.ssh/.prv
	ssh-add ~/.ssh/.guernika.prv
	ssh-add ~/.ssh/shellzor.private
}

export TMPDIR="${HOME}/tmp"
export CVSROOT=/home/mycvs
export PYTHONDOCS=/usr/share/doc/python2/html/
export LANG="es_ES.UTF-8"

SSH_AGENT_PID="$(pgrep ssh-agent)"
if [ -z "${SSH_AGENT_PID}" ]; then
	eval `ssh-agent -s -a ${HOME}/tmp/ssh-agent.sock`
else
	echo "agent pid: $SSH_AGENT_PID"
fi
SSH_AUTH_SOCK=${HOME}/tmp/ssh-agent.sock; export SSH_AUTH_SOCK;


#export PATH=${PATH}:~/bin

export PATH="${PATH}:${HOME:?}/bin/:${HOME}/usr/bin/"

export GIT_EDITOR=vim
export GIT_AUTHOR_IDENT="Jez"
export GIT_PAGER=less

print_err () {
	echo $@
}
wrap_ping () {
	if ! ping -c 1 ${1:?too few arguments} > /dev/null 2>&1 ; then
		print_err "wrap_ping ${1-noaddr} error"
		return 0;
	else
		echo "${1} ok"
	fi
}

net_test () {
	wrap_ping 8.8.8.8
	wrap_ping 172.17.17.9
	wrap_ping 172.17.17.1
	wrap_ping 172.17.17.111
}
net_test;


err_hnd () {
	printf "fatal error! %.20s\n"  "${@}">> /dev/fd/2
	sleep 10;
	exit 3;

}
NS_SRV="172.17.17.111"
my_dig () {
  trap ERR err_hnd;
	set -e
 global NS_SRV
 local default_dns='172.17.17.9'
 local query=${1:?too few args}
 echo "=============================="
 echo "dns query:"
 dig @${qns:=${default_dns}} -t A ${query:?too few args} +ttlid +answer  +nostats +noauthority +noquestion 

}
