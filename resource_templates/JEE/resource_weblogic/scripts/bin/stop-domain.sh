#!/bin/sh

# Start a domain admin server through the node manager.
# The script expects one argument specifying the path to the directory containing install-domain.properties file

# Setup environment
WL_HOME=/opt/oracle/wls_12.1.3/wlserver

if [ -z $1 ]
then
  echo "Usage: $0 <stage dir>"
  exit 0
fi

# Check the os.user property to see if this script has to run as a certain user
OSUSER=$(cat $@/install-domain.properties | awk -F= ' /os.user/ {print tolower($2) } ')

if [ "$OSUSER" = "" ]
then
  # no os.user property found, default to user weblogic
  OSUSER=weblogic
fi

if [ $(whoami) = "$OSUSER" ]
then
  # Copy the wlst module
  rm -f $WL_HOME/common/wlst/modules/prorail_domain*
  cp -f prorail_domain_config.py $WL_HOME/common/wlst/modules

  # Stop the domain
  ${WL_HOME}/common/bin/wlst.sh stop-domain.py $@
else
  echo "You must be user '$OSUSER' to run this script."
  exit 0
fi
