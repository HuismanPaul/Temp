#!/bin/bash
#
# SCRIPT
# linux.sh
#
# SYNOPSIS
# linux.sh -f <file>
#
# DESCRIPTION
# Insert iptables rules (port,protocol and comment) and save the new
# iptables file to satellite configuration channel.
#
# ARGUMENTS
# -f <file> - file containing the depzone user, configuration channel and iptables entries.
#
# NOTES
#   exisiting entries are not modified
#
# The file must contain the following format :
# [project]
# <project name + version>
#
# [channel]
# <appl><type>-6-<version>
# 
# [depzone]
# <depzone>
# 
# [iptables]
# <port>|<prototype>|<comment>
# 25|tcp|mailserver
#
# DEPENDENCIES
#
# RETURN
#
# CHANGELOG
# Date:      By:              Action:
# ---------- ---------------- -----------------------------------
# 01-06-2015 Jurgen Ponds     Create
#
#

################################################################################
# Variable declaration
#
IPTABLES="/etc/sysconfig/iptables"
PASSWORD="redhat"
PROJECT="default"
RET=0
CONF_FILE=""

################################################################################
# function part
#

#
# precheck. Check if file in satellite equals the file on the server
#
function precheck()
{
  rhncfg-client verify $IPTABLES | awk ' { print $1 } ' | grep -q -e modified -e mode -e permission
  if [ $? -eq 0 ]
  then
    printf "File in satellite and on server are different.\nCheck difference before updating."
    messages 2
  fi

  iptables-save | grep -v -e \# -e ^: > /tmp/iptables1
  cat $IPTABLES | grep -v -e \# -e ^: > /tmp/iptables2
  diff /tmp/iptables1 /tmp/iptables2 > /dev/null 2>&1
  R=$?
  rm /tmp/iptables1 /tmp/iptables2 

  if [ $R -eq 1 ]
  then
    printf "Iptables file on server and active iptables configuration\nare different. Check difference before updating."
    messages 2
  fi
}

#
# Check if port is already configured
#
function check_entry()
{
  iptables-save | grep -q -- "--dport $PORT "
  return $?
}

#
# Add entry to iptables
#
function add_entry()
{
  NBR=$(iptables --line-numbers -L | awk ' /reject-with/ { print $1 } ')
  iptables -I RH-Firewall-1-INPUT $NBR \
    -p $PROTO \
    -m $PROTO \
    --dport $PORT \
    -m comment \
    --comment "$COMMENT" \
    -j ACCEPT
  return $?
}

#
# Read firewall entries from the config file.
#
function read_entries()
{
  X=0

  while true
  do
    read line
    [ -z "$line" ] && return
    PORT=$(echo $line | awk -F\| ' { print $1 } ')
    PROTO=$(echo $line | awk -F\| ' { print $2 } ')
    COMMENT=$(echo $line | awk -F\| ' { print $3 } ')
    if ! check_entry
    then
      add_entry
      if [ $? -ne 0 ]
      then
        X=1
      else
        printf "Iptables entry \"$PORT/$PROTO\" added"
        success
        echo
      fi
    else
      printf "Iptables entry \"$PORT/$PROTO\" already exists"
      success
      echo
    fi
  done
  return $X
}

#
# Save the firewall configuration.
#
function save_entry()
{
  printf "Save new iptables configuration"
  cp $IPTABLES $IPTABLES.org
  iptables-save > $IPTABLES
  service iptables restart > /dev/null 2>&1
}

#
# Install the rhn-cfg-management rpm if not installed.
#
function install_rhncfg()
{
  rpm -q rhncfg-management > /dev/null
  if [  $? -eq 1 ]
  then
    printf "package rhncfg-management installed"
    yum -y install rhncfg-management > /dev/null 2>&1
    return $?
  else
    printf "package rhncfg-management already installed"
    return 0
  fi
}

#
# Upload the new firewall configuration in the satellite configuration channel.
#
function upload()
{
  cat $IPTABLES | grep -v -e \# -e ^: > /tmp/iptables1
  cat $IPTABLES.org | grep -v -e \# -e ^: > /tmp/iptables2
  diff /tmp/iptables1 /tmp/iptables2 > /dev/null 2>&1
  R=$?

  rm /tmp/iptables1 /tmp/iptables2

  if [ $R -eq 1 ]
  then
    printf "Config file $IPTABLES uploaded"
    rhncfg-manager update \
      --username $DEPZONE \
      --password $PASSWORD \
      -c $CONFIG $IPTABLES > /dev/null 2>&1
    return $?
  else
    printf "No changes made. No files to upload."
    return 0
  fi
}

#
# Message handling
#
function messages()
{
  R=$1
  case $R in
  0)
    success
    echo 
    echo 
    ;;
  2)
    failure
    echo 
    echo 
    exit $R
    ;;
  *)
    failure
    echo
    echo
    RET=1
    ;;
  esac
}

function header()
{
  clear
  echo "--------------------------------------------------------------------------------"
  echo "Update iptables for $PROJECT"
  echo 
}
################################################################################
# Main script
#

. /etc/rc.d/init.d/functions

while getopts :f: OPT
do
  case "$OPT" in
  f)
    CONF_FILE=$OPTARG
    ;;
  esac
done

if [ -z "$CONF_FILE" ]
then
  echo "No configuration file set"
  exit
fi

#
# Read the config file
#
while read line
do
echo $line
  case $line in
  "[project]")
    read line
    PROJECT=$line
    ;;
  "[channel]")
    read line
    CONFIG=$line
    ;;
  "[depzone]")
    read line
    DEPZONE=$line
    ;;
  "[iptables]")
    header

    precheck

    read_entries
    messages $?
    ;;
  esac
done < $CONF_FILE

save_entry
messages $?

install_rhncfg
messages $?

upload
messages $?

echo "---------------------------------overall result---------------------------------"
printf "Iptables update"
messages $RET
