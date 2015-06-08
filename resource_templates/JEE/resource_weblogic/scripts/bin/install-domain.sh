#!/bin/sh

# Install a new domain directory.
# The installation configures and starts a 'bare' domain including admin server, admin server and machines and snmp monitoring agent (optional).
#
# Creation of clusters, managed servers and other resources on top of this baseline, is up to individual projects
# and can be configured online using the configure-domain script once the admin server is running.
#
# The script expects one argument specifying the path to the domain config install-domain.properties file

if [ -z $1 ]
then
	echo "Usage: $0 <stage dir>"
	exit 0
fi

source /opt/scripts/weblogic/bin/.confdir

# Setup environment
WL_HOME=/opt/oracle/wls_12.1.3/wlserver
DOMAIN=$(cat $CONFDIR/install-domain.properties | awk -F= '/domain.name/ { print $2 } ')
DATADIR=$(cat $CONFDIR/install-domain.properties | awk -F= '/data.root.dir/ { print $2 } ')

if [ $(whoami) = "weblogic" ]
then
	# Copy the wlst module
	rm -f $WL_HOME/common/wlst/modules/prorail_domain*
	cp -f prorail_domain_config.py $WL_HOME/common/wlst/modules

	# Install the domain
	${WL_HOME}/common/bin/wlst.sh install-domain.py $CONFDIR
	if [ $? -ne 0 ]
	then
		exit 1
	fi

	# Tweak for VIEW when nodemanager is running as user root.
	
	mkdir -m750 $DATADIR/weblogic/domains/$DOMAIN/servers/$DOMAIN-adminServer/data/nodemanager
	chown weblogic:weblogic $DATADIR/weblogic/domains/$DOMAIN/servers/$DOMAIN-adminServer/data/nodemanager
else
	echo "You must be user 'weblogic' to run this script."
	exit 0
fi
