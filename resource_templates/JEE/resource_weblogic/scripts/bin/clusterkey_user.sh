#! /bin/bash
# ----------------------------------------------------------------------------
# NAME
#      clusterkey_user.sh - Setup SSH keys for users
#
# SYNOPSIS
#      clusterkey_user.sh [-v] [-h] -u user [-a]
#
# DESCRIPTION
#      Generate SSH DSA key on each cluster node and store that in the
#      authenticated_keys of users on each node.
#
# OPTIONS
#      -a  Setup administrator access to this user account
#      -h  Help message lists options
#      -u user
#          Username that will get exchange SSH keys in the cluster
#      -v  Verbose
#
# AUTHOR
#      M. Meijn, Oracle Corporation
#      2011-12-05   Jurgen Ponds             Split igrid112.env info 2 files: generic and
#                                            specific. Generic is part of build.
#      2012-03-20   Jurgen Ponds             Environment is setup by common.sh script
#      2012-06-26   Jurgen Ponds             Combined createkey_root.sh and createkey_user.sh
#      2012-12-17   Jurgen Ponds             Modified expect commands to work with newer 
#                                            version expect (4.53-0.8)
#
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Initialize generic variables

PRG=$(basename $0 .sh)

function setup_env()
{
	source $(dirname $0)/common.sh
}

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
	echo "usage: clusterkey_root.sh [-v] [-h] -u user [-a]"
}

NAME=""
VERBOSE=false
ROOT=false
OPTERR=0
EXPECT=0
while getopts 'vhu:a' OPTION
do
	case "$OPTION" in
	a)	ROOT=true ;;
	v)	VERBOSE=true ;;
	u)	NAME=$OPTARG ;;
	h)	Usage; exit 0 ;;
	?)	Usage >&2; exit 2 ;;
	esac
done

# Mandatory parameters
[[ -z ${NAME:-} ]] && Usage >&2 && exit 2

setup_env

if [ -z "$LNODE" ]
then
	echo "No local node name LNODE configured"
	echo "Check configuration file"
	exit 2
fi

# Verify if localhost has a domainname suffix
if [ ${LNODE%%.*} == ${LNODE#*.} ]
then
	echo "Use FQDN for local hostname"
	Usage >&2
	exit 3
fi

if [ "$NAME" == "root" ]
then
	REMOTE_PASS=redhat
fi

# ----------------------------------------------------------------------------
# Test/Add RPMs
$VERBOSE && f_hline
$VERBOSE && echo "$PRG: Install expect RPM if it is not installed"

#-------------------------------------------------------------------------------
# Install only if package was not preinstalled.
# At then end it will be removed.
#
if [ "$NAME" == "root" ]
then
	rpm -qa  |grep -q "^expect"
	if [ $? -eq 1 ]
	then
		echo
		echo -n "Install package: expect"
		yum -q -y install expect
		if [ $? -eq 0 ]
		then
			success
			echo
		else
			failure
			echo
		fi
		echo
	else
		EXPECT=1		
	fi
fi

for NODE in $LNODE $RNODES
do
	if [ "$NAME" == "root" ]
	then
		HOMEDIR=/root
	else
		HOMEDIR=/home/$NAME
	fi

	# Verify if remotehost has a domainname suffix
	if [ ${NODE%%.*} = ${NODE#*.} ]
	then
		Usage >&2
		exit 2
	fi

	if [ "$NODE" == "$LNODE" ]
	then
		su - $NAME -c "$PRGBASE/genkey.sh -v"
	else
		#
		# copy scripts to remote hosts
		#
		if [ "$NAME" == "root" ]
		then
			# Use expect to input the root password.
			# This (currently) disables detecting the exit code from the sub-process!
			expect -c "
			spawn scp -q -o StrictHostKeyChecking=no -o PreferredAuthentications=password \
			$HOMEDIR/.ssh/known_hosts $HOMEDIR/.ssh/id_dsa.pub $PRGBASE/genkey.sh \
			$NODE:.
			set timeout 30
			send_user \"DO NOT ENTER A PASSWORD HERE: \"
			sleep 1
			expect {
				\"root@${NODE}'s password:\*\" { send \"${REMOTE_PASS}\r\"; }
			}
			sleep 1
			{interact}
			"
		else
			scp -qp $HOMEDIR/.ssh/known_hosts $HOMEDIR/.ssh/id_dsa.pub $PRGBASE/genkey.sh $NODE:$HOMEDIR/.
			ssh -T $NODE chown $NAME: /home/$NAME /home/$NAME/known_hosts /home/$NAME/id_dsa.pub
		fi

		GENKEY_LOG=/tmp/gen.log
		GENKEY_STAT=/tmp/gen.stat
		if [ "$NAME" == "root" ]
		then
			expect -c "
			spawn ssh -T -o PreferredAuthentications=password $NODE $HOMEDIR/genkey.sh -rv -o $GENKEY_LOG -s $GENKEY_STAT
			set timeout 30
			send_user \"DO NOT ENTER A PASSWORD HERE: \"
			sleep 1
			expect {
				\"$(id -un)@${NODE}'s password:\*\" { send \"${REMOTE_PASS}\r\"; }
			}
			sleep 1
			{interact}
			"
		else
			ssh -T $NODE <<-EOF
				su - $NAME -c "$HOMEDIR/genkey.sh -rv"
				rm -f $HOMEDIR/genkey.sh
			EOF
		fi

		if [ "$NAME" == "root" ]
		then
			# Timing issue somewhere before issueing next ssh
			sync
			sleep 1
			ssh -T $NODE <<-EOF
			if [[ -f $GENKEY_LOG ]]
			then
				cat $GENKEY_LOG
				rm -f $GENKEY_LOG
			fi
			EOF
			GENKEY_RC=$(ssh -T $NODE "cat $GENKEY_STAT && rm -f $GENKEY_STAT") || GENKEY_RC=$?
			if [[ $GENKEY_RC -ne 0 ]]
			then
				echo >&2 "$PRG: genkey failed"
				exit $GENKEY_RC
			fi
		fi

		# ----------------------------------------------------------------------------
		$VERBOSE && f_hline
		$VERBOSE && echo "$PRG: Importing keys from $NODE"
		ssh -T $NODE "rm -f $HOMEDIR/genkey.sh"
		scp -q $NODE:$HOMEDIR/.ssh/known_hosts $NODE:$HOMEDIR/.ssh/id_dsa.pub $HOMEDIR/.
		cp -f $HOMEDIR/known_hosts $HOMEDIR/.ssh/known_hosts

		if grep -qs -f $HOMEDIR/id_dsa.pub $HOMEDIR/.ssh/authorized_keys
		then
			$VERBOSE && echo "$PRG: Public SSH key from $NODE already exists in $HOMEDIR/.ssh/authorized_keys. Not updated."
		else
			cat $HOMEDIR/id_dsa.pub >> $HOMEDIR/.ssh/authorized_keys
		fi

		rm -f $HOMEDIR/id_dsa.pub $HOMEDIR/known_hosts
	fi

	# Last trick.
	# May decide later if you want to leave this hole open.
	# Alternative is to use xauth, but that has its limitations.
	if $ROOT
	then
		# Enable root to ssh to $NAME@$LNODE
		if ! grep -qs -f $HOME/.ssh/id_dsa.pub $HOMEDIR/.ssh/authorized_keys
		then
			$VERBOSE && echo "$PRG: Copying root Public key to $NAME authorized_keys on local $LNODE"
			cat $HOME/.ssh/id_dsa.pub >> $HOMEDIR/.ssh/authorized_keys
		else
			$VERBOSE && echo "$PRG: Public key of root already exists in authorized_keys on $LNODE. Not updated."
		fi

		# Enable root to ssh to $NAME@$NODE
		scp -q $HOME/.ssh/id_dsa.pub $NODE:$HOMEDIR/.ssh/id_dsa.pub.root
		if ! ssh $NODE "grep -qs -f $HOMEDIR/.ssh/id_dsa.pub.root $HOMEDIR/.ssh/authorized_keys"
		then
			$VERBOSE && echo "$PRG: Copying root pub key to $NAME authorized_keys on remote $NODE"
			ssh -T $NODE "cat $HOMEDIR/.ssh/id_dsa.pub.root >> $HOMEDIR/.ssh/authorized_keys"
		else
			$VERBOSE && echo "$PRG: Public key of root already exists in authorized_keys on $NODE. Not updated."
		fi
		ssh -T $NODE "rm -f $HOMEDIR/.ssh/id_dsa.pub.root"
	fi
done

if [ "$NAME" == "root" ]
then
	#-------------------------------------------------------------------------------
	# Remove only if package was not preinstalled.
	#
	if [ $EXPECT -eq 0 ]
	then
		echo
		echo -n "Remove package: expect"
		yum -q -y remove expect
		if [ $? -eq 0 ]
		then
			success
			echo
		else
			failure
			echo
		fi
		echo
	fi
fi

# ----------------------------------------------------------------------------
$VERBOSE && f_hline
$VERBOSE && echo "$PRG: Done"
trap - EXIT
exit 0
