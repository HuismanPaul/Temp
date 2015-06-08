#!/bin/bash
#
# Convenience scripts for TIBCO tools and services.
# Purpose:
#   Runs commandline based EMS administration client.

. `dirname $0`/setenv.sh

$EMS_HOME/bin/tibemsadmin $*
