#!/bin/bash
#
# NAME
#      weblogic.sh - Configure 12c domains
#
# SYNOPSIS
#      weblogic.sh
#
# DESCRIPTION
#      Universal install script for Oracle Weblogic
#      weblogic installation
#
# NOTES
#      Must run as root
#
# CHANGELOG
#      Date:       By:            Action:
#      -----------  ------------------- --------------------------------------------------------------------------------
#      2015-06-01   Paul Huisman  Initial build for WebLogic 12.1.3 (12c)
#
# FILES
#      Set all variables in ${PRGBASE}/scripts
#

################################################################################
# Section: Check installation environment
#
function setup_env()
{
  # ----------------------------------------------------------------------------
  # Load common functions and settings
  #
  source $(dirname $0)/common.sh
  source $(dirname $0)/error.sh
  LOG=/tmp/weblogic-$$.log
  templogfile $LOG
}

# ----------------------------------------------------------------------------
# Distribute ssh key between the install node and other domain nodes
#
function distribute_keys()
{
  if [ ! -f /tmp/.clusterkey ]
  then
    cat <<-EOF >> $LOG

    Distribute ssh keys
    +------------------------------------------------------------------------------+
    $(date)

EOF

    echo "Distribute ssh key"
    echo
    clusterkey_user.sh -v -u root >> $LOG
    touch /tmp/.clusterkey
  fi
}

# ----------------------------------------------------------------------------
# Check availablilty of the Weblogic nodes
#
function nodes_available()
{
  # --------------------------------------------------------------------
  # Check availablilty with a ping test to all servers
  # A server must responsed within 2 counts.
  #
  A=0

  for NODE in $NODES
  do
    echo -n "Node $NODE available"
    ping -q -c 2 $NODE > /dev/null
    if [ $? -eq 0 ]
    then
      success
      echo
    else
      failure
      echo
      A=1
    fi
  done
  if [ $A -ne 0 ]
  then
    echo -n "Not all nodes available."
    failure
    echo
    exit
  fi
}

# ----------------------------------------------------------------------------
# Check the prerequisistes for the weblogic installation.
# - nodes available
# - distribute ssh keys for system checks
# - group name: weblogic
# - user name: weblogic
# - ownership on directories: /opt/oracle $DOMAINBASE $WL_LOG
# - limits.conf settings
# - kernel parameter settings (sysctl)
# - availability of properties files
#
function prerequisistes()
{
  kop "Prerequisites"
  header "Check prerequisistes"
  echo
  echo

  if [ ! -f $CONFDIR/install-domain.properties ]
  then
    echo "$CONFDIR/install-domain.properties doesn't exist."
    exit
  fi

  if [ ! -f $CONFDIR/configure-domain.properties ]
  then
    echo "$CONFDIR/configure-domain.properties doesn't exist."
    exit
  fi

  nodes_available
  echo
  distribute_keys

  Q=0
  for NODE in $NODES
  do
    X=0
    G=0
    echo -n "+-- Check groups"
    for group in weblogic
    do
      ssh $NODE "cat /etc/group | awk -F: ' { printf \$1 } ' | grep -q $group"
      if [ $? -ne 0 ]
      then
        echo -n "Group $group not available"
        failure
        echo
        X=1;G=1
      fi
    done
    [ $G -eq 0 ] && success;echo

    U=0
    echo -n "+-- Check users"
    for passwd in weblogic
    do
      ssh $NODE "cat /etc/passwd | awk -F: ' { printf \$1 } ' | grep -q $passwd"
      if [ $? -ne 0 ]
      then
        [ $U -eq 0 ] && echo
        echo -n "User $passwd not available"
        failure
        echo
        X=1;U=1
      fi
    done
    [ $U -eq 0 ] && success;echo
    echo
  done
  if [ $Q -eq 1 ]
  then
    exitcode 40
  else
    exitcode 41
  fi
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

# ----------------------------------------------------------------------------
# Perform start domain
#
function start_domain()
{
  header "Start domain $WLDOM"
  echo
  echo
  #STARTING THE NODEMANAGER
  /opt/weblogic/domains/$DOMAIN/bin/startNodeManager.sh &

  su - $OS_USER <<-EOL 2> /dev/null >> $LOG
    cd $PRGBASE
    ./start-domain.sh $CONFDIR
EOL
  if [ $? -ne 0 ]
  then
    exitcode 22
  else
    exitcode 23
  fi
}

# ----------------------------------------------------------------------------
# Perform stop domain
#
function stop_domain()
{
  su - $OS_USER <<-EOL 2> /dev/null >> $LOG
  echo
  echo "Stop domain $WLDOM"
  echo "+------------------------------------------------------------------------------+"
  date
  echo
  cd $PRGBASE
  ./stop-domain.sh $CONFDIR
EOL
  if [ $? -ne 0 ]
  then
    exitcode 24
  else
    exitcode 25
  fi
}


# start a nodemanager, $1: wls or wsm
#
function start_nodemanager()
{
  for NODE in $NODES
  do
    ssh -T $NODE <<-EOF
    service ${TYPE}nodemanager start
    sleep 4
    service ${TYPE}nodemanager status
EOF
  done
}

# ----------------------------------------------------------------------------
# stop a nodemanager, $1: wls or wsm
#
function stop_nodemanager()
{
  for NODE in $NODES
  do
    ssh -T $NODE <<-EOF
    service ${TYPE}nodemanager stop
    sleep 4
    service ${TYPE}nodemanager status
EOF
  done
}

# ----------------------------------------------------------------------------
# restart a nodemanager, $1: wls or wsm
#
function restart_nodemanager()
{
  header "Restart wlsnodemanagers"
  echo
  echo
  for NODE in $NODES
  do
     kop "$NODE"
     ssh -T $NODE <<-EOF 2>> $LOG
     service ${TYPE}nodemanager stop
     sleep 4
     service ${TYPE}nodemanager start
     sleep 4
     service ${TYPE}nodemanager status
EOF
  done
}


# ----------------------------------------------------------------------------
# Perform install domain for WebLogic 12c
#
function install_domain()
{
  if [ -d $DOMAINBASE/domains/$WLDOM ]
  then
    kop "Domain $WLDOM is already installed"
    ps -ef | grep -q adminServe[r]
    if [ $? -ne 0 ]
    then
      start_domain
    else
      exitcode 28
    fi
  else
    su - weblogic <<-EOL >> $LOG
    echo
    echo "Install domain $WLDOM"
    echo "+------------------------------------------------------------------------------+"
    date
    echo
    cd $PRGBASE
    ./install-domain.sh $PROPBASE
EOL
    if [ $? -ne 0 ]
    then
      exitcode 20
    else
      exitcode 21
      start_domain
    fi
  fi
}

# ----------------------------------------------------------------------------
# Perform configure 12c domain
#
function configure_domain()
{
  su - weblogic <<-EOL >> $LOG
    echo
    echo "Configurure domain $WLDOM"
    echo "+------------------------------------------------------------------------------+"
    date
    echo
    cd $PRGBASE
    ./configure-domain.sh $PROPBASE
EOL
  if [ $? -ne 0 ]
  then
    exitcode 26
  else
    exitcode 27
  fi
}

# ----------------------------------------------------------------------------
# Perform distribute domain
#
function distribute_domain()
{
  # ----------------------------------------------------------------------------
  # If $DOMAINBASE is installed on a local filesystem/directory, distribute
  # the domain to other servers.
  #
  # In case of an GFS2 filesystem, no distribution required.
  #
  df -TP $DOMAINBASE | grep -q gfs2
  if [ $? -ne 0 ]
  then

    cat <<-EOF >> $LOG
    +------------------------------------------------------------------------------+
    $(date)

EOF

    echo "Starting to pack domain "$WLDOM" in $DOMAINBASE/domains/"$WLDOM".jar"
    if [ -f $DOMAINBASE/domains/$WLDOM.jar ] ; then
      echo "Template jar exists, deleting..." >> $LOG
      rm  $DOMAINBASE/domains/$WLDOM.jar
    fi

    printf "Package domain $WLDOM "
    /opt/oracle/middleware/wlserver_10.3/common/bin/pack.sh -domain=$DOMAINBASE/domains/$WLDOM/ -template=$DOMAINBASE/domains/$WLDOM.jar -template_name=$WLDOM -managed=true >> $LOG
    if [ $? -eq 0 ]
    then
      echo "Domain packed. Starting to distribute to nodes: $RNODES" >> $LOG
      exitcode 42
    else
      echo "Domain packed failed" >> $LOG
      exitcode 43
    fi

    for NODE in $RNODES
    do
      X=0
      echo "Create remote target directory"
      ssh -T $NODE <<-EOF >> $LOG
      mkdir -p $DOMAINBASE/domains
      chown weblogic:weblogic $DOMAINBASE/domains
EOF

      scp $DOMAINBASE/domains/$WLDOM.jar $NODE:$DOMAINBASE/domains >> $LOG
      if [ $? -ne 0 ]
      then
        printf "Remote copy to $NODE failed "
        failure
        echo
        X=1
      else
        printf "Distribute domain $WLDOM to node $NODE "
        ssh -T $NODE <<-EOF >> $LOG
          date
          echo "Done ssh"
          chown weblogic:weblogic $DOMAINBASE/domains/$WLDOM.jar
          su - weblogic
          echo "Done su -"
          cd $DOMAINBASE/domains/
          if [ -d $WL_LOG/domains/$WLDOM ]
          then
            echo "Log directory already exists"
          else
            echo " Creating Log directory"
            mkdir $WL_LOG/domains/$WLDOM
          fi

          if [ -d $DOMAINBASE/domains/$WLDOM ]
          then
            echo "Domain directory already exists, deleting..."
            rm -rf $DOMAINBASE/domains/$WLDOM
          fi

          echo "Unpack domain $WLDOM at node $NODE"
          /opt/oracle/middleware/wlserver_10.3/common/bin/unpack.sh -template=$DOMAINBASE/domains/$WLDOM.jar -domain=$DOMAINBASE/domains/$WLDOM
          rm $DOMAINBASE/domains/$WLDOM.jar
EOF
        if [ $? -eq 0 ]
        then
          success
          echo
        else
          failure
          echo
          X=1
        fi
      fi
    done
    [ -f $DOMAINBASE/domains/$WLDOM.jar ] && rm $DOMAINBASE/domains/$WLDOM.jar
  fi
}

# ----------------------------------------------------------------------------
# Perform enroll domain
#
function enroll_domain()
{
  header "Enroll domain $WLDOM"
  echo
  echo

  FAILED=0
  for BOOT in $DOMAINBASE/domains/$WLDOM/servers/$WLDOM-*/data/nodemanager/
  do
    if [ -f $BOOT/boot.properties ]
    then
      SERVER=$(echo $BOOT | sed -e 's+.*servers/++g' -e 's+/data.*++g')
      exitcode 30
    else
      FAILED=1
    fi
  done
  if [ $FAILED -eq 1 ]
  then
    stop_domain
    RET=$?
    if [ $RET -eq 0 ]
    then
      for NODE in $NODES
      do
        ssh -T $NODE <<-EOF >> $LOG
          echo
          echo "Enroll domain $WLDOM"
          echo "+------------------------------------------------------------------------------+"
          date
          echo
          su - weblogic <<-EOL
            cd $DOMAINBASE/domains/$WLDOM
            $PRGBASE/enroll-domain.sh $PRGBASE/enroll-domain.py $PROPBASE
EOL
EOF
        if [ $? -ne 0 ]
        then
          exitcode 31
        else
          exitcode 32
        fi
      done
    fi
  fi
}

function clean_up()
{
  rm -f .domain
}

# ----------------------------------------------------------------------------
# Show usage
#
function usage()
{
clear

echo "Weblogic domain scripting" | tr [:lower:] [:upper:]

cat <<-EOF
--------------------------------------------------------------------------------
The weblogic scripting enables the user to install and configure
a weblogic environment.

EOF
cat <<-EOF

--------------------------------------------------------------------------------

Usage: $(basename $0) <option> <configPath>

Domain options:
    installDomain            Configure the Weblogic Domain conform the
                             configure-domain.properties and the
                             install-domain.properties.

Other options:
    usage                    Shows this usage


EOF

}

################################################################################
# Main script
#

# ----------------------------------------------------------------------------
# Must run as root.
#
if [ "$USER" != "root" ]
then
  echo >&2 "$PRG: must be run as root"
  exit 1
fi

if [ -z "$1" ]
then
  usage
  exit
fi

if [ -z "$2" ]
then
  usage
  exit
fi

if [ -n "$2" ]
then
  CONFDIR=$2
  echo CONFDIR=$CONFDIR > .confdir
fi


case $1 in
  installDomain)
    setup_env
    prerequisistes
    #distribute_keys
    #activate_rngd
    install_domain
    configure_domain
    enroll_domain
    #kill_rngd
    clean_up
           ;;
  usage|*)
    usage
    exit
    ;;
esac

f_hline
exit



