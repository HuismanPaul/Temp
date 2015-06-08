#! /bin/bash
# ----------------------------------------------------------------------------
# NAME
#      clusterkey_root.sh - Setup SSH keys for root
#
# SYNOPSIS
#      clusterkey_root.sh [-v] [-h]
#
# DESCRIPTION
#      Generate SSH DSA key on each cluster node and store that in the
#      authenticated_keys of root on each node.
#
# OPTIONS
#      -h  Help message lists options
#      -v  Verbose
#
# AUTHOR
#      M. Meijn, Oracle Corporation
#      2011-12-05   Jurgen Ponds             Split igrid112.env info 2 files: generic and
#                                            specific. Generic is part of build.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Initialize generic variables

PRG=$(basename $0 .sh)

function setup_env()
{
	source $(dirname $0)/common.sh
}

# ----------------------------------------------------------------------------
# Setup trap for diagnosis
#trap 'echo $PRG[$LINENO]: Exit $?' EXIT

# ----------------------------------------------------------------------------
# Must run as root.
if [ "$USER" != "root" ]
then
        echo >&2 "$PRG: must be run as root"
        exit 1
fi

# ----------------------------------------------------------------------------
# Argument parsing
#
Usage()
{
	echo "usage: clusterkey_root.sh [-v] [-h]"
}


VERBOSE=false
OPTERR=0
while getopts 'vh' OPTION
do
	case "$OPTION" in
	v)	VERBOSE=true ;;
	h)	Usage; exit 0 ;;
	?)	Usage >&2; exit 2 ;;
	esac
done

setup_env

# Verify if localhost has a domainname suffix
if [ ${LNODE%%.*} = ${LNODE#*.} ]
then
	Usage >&2
	exit 2
fi

for RNODE in $LNODE $RNODES
do
	# Verify if remotehost has a domainname suffix
	if [ ${RNODE%%.*} = ${RNODE#*.} ]
	then
		Usage >&2
		exit 2
	fi

	# ----------------------------------------------------------------------------
	# Read remote root password from the command line
	while [ -z ${REMOTE_PASS:-} ]
	do
		read -s -a REMOTE_PASS -p "Enter password for root on remote node(s): " || exit 1
		echo
		echo
	done

	# ----------------------------------------------------------------------------
	# Test/Add RPMs
	$VERBOSE && f_hline
	$VERBOSE && echo "$PRG: Install expect RPM if it is not installed"
	yum -qy install expect

	# ----------------------------------------------------------------------------
	# SSH key setup for root
	$VERBOSE && f_hline
	$VERBOSE && echo "$PRG: Generating keys for $(id -un) on local node"
	$PRGBASE/genkey.sh -v

	# Use expect to input the root password.
	# This (currently) disables detecting the exit code from the sub-process!
	expect <<-EOF - scp -q -o StrictHostKeyChecking=no -o PreferredAuthentications=password \
		$HOME/.ssh/known_hosts $HOME/.ssh/id_dsa.pub $PRGBASE/genkey.sh \
		$RNODE:
	set timeout 30
	eval spawn \$argv
	send_user "DO NOT ENTER A PASSWORD HERE: "
	sleep 1
	expect "$(id -un)@${RNODE}'s password:*"
	sleep 1
	send "${REMOTE_PASS}\r"
	sleep 1
	interact
	EOF

	GENKEY_LOG=/tmp/gen.log
	GENKEY_STAT=/tmp/gen.stat
	expect <<-EOF - ssh -o PreferredAuthentications=password $RNODE $HOME/genkey.sh -rv -o $GENKEY_LOG -s $GENKEY_STAT
	set timeout 30
	eval spawn \$argv
	send_user "DO NOT ENTER A PASSWORD HERE: "
	sleep 1
	expect "$(id -un)@${RNODE}'s password:*"
	sleep 1
	send "${REMOTE_PASS}\r"
	sleep 1
	interact
	EOF

	# Timing issue somewhere before issueing next ssh
	sync
	sleep 1
	ssh $RNODE "if [[ -f $GENKEY_LOG ]]
	then
		cat $GENKEY_LOG
		rm -f $GENKEY_LOG
	fi"
	GENKEY_RC=$(ssh $RNODE "cat $GENKEY_STAT && rm -f $GENKEY_STAT") || GENKEY_RC=$?
	if [[ $GENKEY_RC -ne 0 ]]
	then
		echo >&2 "$PRG: genkey failed"
		exit $GENKEY_RC
	fi

	# ----------------------------------------------------------------------------
	$VERBOSE && f_hline
	$VERBOSE && echo "$PRG: Importing keys from $RNODE"
	ssh $RNODE "rm -f $HOME/genkey.sh"
	scp -q $RNODE:.ssh/known_hosts $RNODE:.ssh/id_dsa.pub $HOME/.
	cp -f $HOME/known_hosts $HOME/.ssh/known_hosts

	if grep -qs -f $HOME/id_dsa.pub $HOME/.ssh/authorized_keys
	then
		$VERBOSE && echo "$PRG: Public SSH key from $RNODE already exists in $HOME/.ssh/authorized_keys. Not updated."
	else
		cat $HOME/id_dsa.pub >> $HOME/.ssh/authorized_keys
	fi

	rm -f $HOME/id_dsa.pub $HOME/known_hosts
done

# ----------------------------------------------------------------------------
$VERBOSE && f_hline
$VERBOSE && echo "$PRG: Done"
trap - EXIT
exit 0
