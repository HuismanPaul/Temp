#!/bin/sh

# Configure a freshly installed and started domain.
# This configuration is project specific,
# The script expects one argument specifying the path to the directory containing configure-domain.properties
#	and install-domain.properties file

# Setup environment
WL_HOME=/opt/oracle/wls_12.1.3/wlserver/

source /opt/scripts/weblogic/bin/.confdir

if [ "$(whoami)" == "weblogic" ]
then
	# Copy the wlst module
	rm -f $WL_HOME/common/wlst/modules/prorail_domain*
	cp -f prorail_domain_config.py $WL_HOME/common/wlst/modules
	
	# Configure the domain from the config domain properties
	${WL_HOME}/common/bin/wlst.sh configure-domain.py $CONFDIR
	if [ $? -ne 0 ]
	then
		exit 1
	fi
else
	echo "You must be user 'weblogic' to run this script."
	exit 0
fi
