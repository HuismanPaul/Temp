#!/bin/bash
#
# Convenience scripts for TIBCO tools and services.
# Purpose:
#   Sets up TIBCO environment based on given TIBCOSTACK.

TIBCO_HOME=/opt/tibco

if [ -z $TIBCOSTACK ]; then
# Default TIBCOSTACK is ESB2.0
  TIBCOSTACK="ESB2.0"
fi

# These settings are for ESB 1.0 (BW 5.7)
if [ $TIBCOSTACK == ESB1.0 ]; then
  TIBRV_VERSION=8.1
  TRA_VERSION=5.6
  EMS_VERSION=5.1
  ADMIN_VERSION=5.6
  DESIGNER_VERSION=5.6
  BW_VERSION=5.7
# These settings are for ESB 2.0 (BW 5.9)
elif [ $TIBCOSTACK == ESB2.0 ]; then
  TIBRV_VERSION=8.3
  TRA_VERSION=5.7
  EMS_VERSION=5.1
  ADMIN_VERSION=5.7
  DESIGNER_VERSION=5.7
  BW_VERSION=5.9
else
  echo "Unknown ESB stack"
  exit 1
fi

TRA_HOME=$TIBCO_HOME/tra/$TRA_VERSION
RV_HOME=$TIBCO_HOME/tibrv/$TIBRV_VERSION
EMS_HOME=$TIBCO_HOME/ems/$EMS_VERSION
ADMIN_HOME=$TIBCO_HOME/administrator/$ADMIN_VERSION
DESIGNER_HOME=$TIBCO_HOME/designer/$DESIGNER_VERSION
BW_HOME=$TIBCO_HOME/bw/$BW_VERSION
GH_HOME=/opt/greenhat

# Others
BUILD_HOME=$HOME/build
if [ -z "$TIBCO_BIN" ]; then
  TIBCO_BIN=$TIBCO_HOME/bin
fi

# Derived settings
EMSNAME=$EMS_HOME/bin/tibemsd
CMD=`basename $0 .sh`

export PATH=$PATH:$RV_HOME/bin
export LD_LIBRARY_PATH=$TIBCO_HOME/lib:$RV_HOME/lib:$LD_LIBRARY_PATH
