#!/bin/sh

# Enroll a new domain on a machine.
# The domain enrollment needs to take place after starting the admin server. The script needs to run once on every machine of the domain. 
# It will make the machine node manager aware of the new domain existence and location.  
#
# The script expects one argument specifying the path to the domain config install-domain.properties file

# Setup environment
WL_HOME=/opt/oracle/wls_12.1.3/wlserver/
 
source /opt/scripts/weblogic/bin/.confdir

if [ $(whoami) = "weblogic" ]
then
  # Copy the wlst module
  rm -f $WL_HOME/common/wlst/modules/prorail_domain*
  cp -f ${0%/*}/prorail_domain_config.py $WL_HOME/common/wlst/modules

  # Enroll the domain
  ${WL_HOME}/common/bin/wlst.sh $CONFDIR
else
  echo "You must be user 'weblogic' to run this script."
  exit 0
fi
