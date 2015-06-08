#!/bin/bash
#
# NAME
#      common.sh - commonly used functions and environment settings
#
# SYNOPSIS
#      common.sh
#
# DESCRIPTION
#      The installation scripts all use same functions. These functions
#      are collected in this script. 
#
# NOTES
#      Must run as root
#
# CHANGELOG
#      Date:	By:		      Action:
#      -----------  ------------------------ -------------------------------------------
#      2012-01-11   Jurgen Ponds	     Initial build
# 10-18
#      2013-04-03   Jurgen Ponds             Added new Variables: DOMAINBASE, APPLOG, WL_LOG
#                                            Create $DOMAINLOG/$WLDOM. Normally starting a managed server will do this, but
#                                            when specifying a logdir in the java startup variables, it will initially fail to start.
#      2013-06-28   Jurgen Ponds             Moved WL_HOME from weblogic.sh to common.sh

#
# FILES
#      Set all variables in ${PRGBASE}/etc
#

function f_hline()
{
	echo '+------------------------------------------------------------------+'
}

# ------------------------------------------------------------------------------
# Show header with time stamp.
#
function header()
{
	echo
	f_hline
	date
	echo -n "$1"
}

# ------------------------------------------------------------------------------
# Show header text in uppercase
#
function kop()
{
	echo
	echo "$1" | tr [:lower:] [:upper:]
	echo "-------------------------------------"
	echo
}

# ------------------------------------------------------------------------------
# Show location of install/remove logfile
#
function templogfile()
{
	f_hline
	echo
	echo "View installation progress in: $1"
	echo
	f_hline
}

function checkvar()
{
	eval V='$'$1
	if [ -z "$V" ]
	then
		echo -n "Variable $1 not set"
		failure
		echo
		X=1
	fi
}

# ------------------------------------------------------------------------------
# Parse the install en config properties files and set the variables 
# for the weblogic installation
#
function set_weblogic_env()
{
	# ----------------------------------------------------------------------------
	# Source the install-domain.properties file. The xml file is parsed and 
	# translated to shell variables.
	#
	cat $PROPFILE | awk -F= ' !/#|^$/ {gsub("[.]","_",$1); printf("%s=%s\n",$1,$2) } '> /tmp/install.prop
	source /tmp/install.prop 2>/dev/null

	# ----------------------------------------------------------------------------
	# Check variables
	#
	X=0
	echo "Check variables in install-domain.properties"
	echo "------------------------------------------------------------------------------"
	checkvar domain.name
	checkvar machines
	checkvar machine.domain
	checkvar admin.server.address
	echo

	if [ $X -eq 1 ]
	then
		exit
	fi

	echo "Set os.user"
	if [ -n "$os_user" ]
	then
		OS_USER=$os_user
	fi

	# ----------------------------------------------------------------------------
	# Check domain
	#
	echo -n "Check domain"
	WLDOM=$domain_name
	PROPBASE=/mnt/$domain_name/stage

	NODES=$(echo $machines | sed 's/,/ /g')
	echo $NODES | grep -q $admin_server_address
	if [ $? -eq 1 ]
	then
		NODES="$admin_server_address $NODES"
	fi
	ANODES=$(echo $NODES | sed -e "s/$admin_server_address[ ]*//g" -e 's/,/ /g')

	RNODES=""
	LNODE=$admin_server_address.$machine_domain
	for NODE in $ANODES
	do
		echo RNODE | grep $admin_server_address -q
		if [ $? -ne 0 ]
		then
			RNODES="$RNODES $NODE.$machine_domain "
		fi
	done
}

# ----------------------------------------------------------------------------
# Set common environment variables required for the installation
#
function set_environment()
{
	# ----------------------------------------------------------------------------
	# source function library
	#
	. /etc/rc.d/init.d/functions
	BOOTUP=color
	
	# ----------------------------------------------------------------------------
	# Tunable parameters and their default:
	#
	BASE=$(echo $PWD | awk -F/ ' { print $4 } ')
	SOFTWARE=Weblogic
	PRGBASE=/opt/scripts/weblogic/bin/
	CONFBASE=/opt/testapp/wls/config.1/
	WL_LOG=/var/log/weblogic
	WL_HOME=/opt/oracle/wls_12.1.3/wlserver
	WL_EXTLIB=/opt/oracle/wls_12.1.3/extlib
	WSM=""
	TYPE=wls
	PATH=$PATH:$PRGBASE:/usr/local/bin
	PRORAIL_RELEASE=/etc/prorail-release
	OS_USER=weblogic
	ACTIONAL_VERSION=""
	TIBCOLIB_VERSION=""

  # ----------------------------------------------------------------------------
  # Check if environment file is available.
  #
  source $PRGBASE/.confdir

	# ----------------------------------------------------------------------------
	# Check if environment file is available.
	#
	PROPFILE=$CONFDIR/install-domain.properties

	set_weblogic_env
	DOMAINBASE=$data_root_dir/weblogic

	# ----------------------------------------------------------------------------
	# During software installation this will be ignored.
	# During maintaintance tasks, it will be used to set the WSM and TYPE variable.
	#
	if [ -f $CONFDIR/configure-domain.properties ]
	then
		WSM=$(cat $CONFDIR/configure-domain.properties | awk -F= ' /^cluster.type=/ { print $2 } ')
		if [ "$WSM" == "wsm" ]
		then
			TYPE=wsm
		else
			TYPE=wls
		fi
	fi

	if [ -n "$WEBLOGIC_VERSION" ]
	then
		WEBLOGICRELEASE=${WEBLOGIC_VERSION##*-}
		WEBLOGICVERSION=${WEBLOGIC_VERSION}
	fi
	if [ -n "$PRORAIL_VERSION" ]
	then
		SCRIPTRELEASE=${PRORAIL_VERSION##*-}
		SCRIPTVERSION=${PRORAIL_VERSION}
	fi
	if [ -n "$CONFIG_VERSION" ]
	then
		PROJECTRELEASE=${CONFIG_VERSION##*-}
		PROJECTVERSION=${CONFIG_VERSION}
	fi
	if [ -n "$ACTIONAL_VERSION" ]
	then
		ACTIONALRELEASE=${ACTIONAL_VERSION##*-}
		ACTIONALVERSION=${ACTIONAL_VERSION}
	fi
	if [ -n "$TIBCOLIB_VERSION" ]
	then
		TIBCOLIBRELEASE=${TIBCOLIB_VERSION##*-}
		TIBCOLIBVERSION=${TIBCOLIB_VERSION}
	fi
	if [ -n "$SINGLETON_VERSION" ]
	then
		SINGLETONLIBRELEASE=${SINGLETONLIB_VERSION##*-}
		SINGLETONLIBVERSION=${SINGLETONLIB_VERSION}
	fi
}

function echo_good()
{
	TEXT=$1
        RES_COL=$2
        MOVE_TO_COL="echo -en \\033[${RES_COL}G"
        [ "$BOOTUP" = "color" ] && $MOVE_TO_COL
        [ "$BOOTUP" = "color" ] && $SETCOLOR_SUCCESS
        echo -n "$TEXT"
        [ "$BOOTUP" = "color" ] && $SETCOLOR_NORMAL
        echo -ne "\r"
        return 0
}

function echo_error()
{
	TEXT=$1
        RES_COL=$2
        MOVE_TO_COL="echo -en \\033[${RES_COL}G"
        [ "$BOOTUP" = "color" ] && $MOVE_TO_COL
        [ "$BOOTUP" = "color" ] && $SETCOLOR_FAILURE
        echo -n "$ERROR"
        [ "$BOOTUP" = "color" ] && $SETCOLOR_NORMAL
        echo -ne "\r"
        return 1
}

# ----------------------------------------------------------------------------
# Progress bar
#
function waits()
{
	PD=$1

	TIME="0.1"
	setterm -cursor off
	echo

	while true
	do
		for i in {2..77} {77..2}
		do
			ps -eo pid  | grep -q "^[ ]*${PD}$"
			if [ $? -eq 0 ]
			then
				RES_COL=$i
				echo -ne "\r\E[K"
				MOVE="echo -en \\033[${RES_COL}G"
				echo -ne "+----------------------------------------------------------------------------+"
				$MOVE
				printf "#"
				sleep $TIME
				D=1
			else	
				D=0
			fi
		done
		[ $D -eq 0 ] && break
	done
	printf "\n\n\n"
	setterm -cursor on
}

set_environment
