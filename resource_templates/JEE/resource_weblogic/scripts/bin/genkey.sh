#! /bin/bash

# OPTIONS
#      -l is the default

# ----------------------------------------------------------------------------
# Initialize generic variables
#set -o nounset -o errexit
PRG=${0##*/}
PRG=${PRG%.*}

# ----------------------------------------------------------------------------
# Setup trap for diagnosis
trap 'echo >&2 $PRG[$LINENO]: Exit $?' EXIT HUP INT QUIT TERM

# ----------------------------------------------------------------------------
# Argument parsing

Usage()
{
    echo "usage: $PRG.sh [-v] [-h] [-o logfile] [-s statfile] -l | -r"
}

LOCAL=false
REMOTE=false
VERBOSE=false
OPTERR=0
while getopts 'o:s:lrvh' OPTION; do
  case "$OPTION" in
  o)  LOGFILE="$OPTARG" ;;
  s)  STATFILE="$OPTARG" 
    touch $STATFILE
    ;;
    l)  LOCAL=true ;;
    r)  REMOTE=true ;;
    v)  VERBOSE=true ;;
    h)  Usage; exit 0 ;;
    ?)  Usage >&2; exit 2 ;;
  esac
done

# Flags are mutual exclusive
if $LOCAL && $REMOTE; then
  echo >&2 Usage
  exit 2
fi

# Check argument format
LNODE=$(hostname)
if [[ ${LNODE%%.*} = ${LNODE#*.} ]]; then
  echo >&2 "$PRG: $hostname is not in hostname.domain.name format"
  exit 2
fi

# Redirecting to log file
if [[ ! -z ${LOGFILE:-} ]]; then
  exec > $LOGFILE 2>&1
fi

if [[ ! -z ${STATFILE:-} ]]; then
  trap 'echo $? >$STATFILE; echo >&2 $PRG[$LINENO]: Exit $(<$STATFILE)' EXIT HUP INT QUIT TERM
fi

learn_host()
{
  DEST_HOST=$1
  ((RC=0))
  KEYGEN_OUT=$(ssh-keygen 2>/dev/null -R $DEST_HOST) || ((RC=$?))
  if [[ $RC -ne 0 ]]; then
    echo >&2 "$PRG: ssh-keygen failed."
    return $RC
  fi
  
  # Catch result code in case $DEST_HOST is not resolved.
  ((RC=0))
  SSH_OUTPUT=$(ssh -o StrictHostKeyChecking=no $DEST_HOST true 2>&1) || ((RC=$?))
  # Elegant output: Hide Warning
  [[ ! -z $SSH_OUTPUT ]] && (echo "$SSH_OUTPUT" | sed 's/^Warning: //')
  return $RC
}

# ----------------------------------------------------------------------------
# Main
$VERBOSE && echo "$PRG: Creating SSH config for $(id -un)@${LNODE} on host $(hostname)"
if [[ ! -d $HOME/.ssh ]]; then
  mkdir $HOME/.ssh
  chmod 700 $HOME/.ssh
fi

# ----------------------------------------------------------------------------
# Check if already generated.
# Possibly delete from keys using:
# sed -i "/ $(id -un)@${LNODE}$/d" $HOME/.ssh/authorized_keys
if grep -qs "$(id -un)@${LNODE}$" $HOME/.ssh/id_dsa.pub; then
  $VERBOSE && echo "$PRG: Public SSH key for $(id -un)@${LNODE} already exists in $HOME/.ssh/id_dsa.pub. Not updated."
else
  $VERBOSE && echo "$PRG: Generating DSA key"
  rm -f $HOME/.ssh/id_dsa $HOME/.ssh/id_dsa.pub
  ssh-keygen -q -t dsa -f $HOME/.ssh/id_dsa -N ''
fi
if grep -qs -f $HOME/.ssh/id_dsa.pub $HOME/.ssh/authorized_keys; then
  $VERBOSE && echo "$PRG: Public SSH key for $(id -un)@${LNODE} already exists in $HOME/.ssh/authorized_keys. Not updated."
else
  $VERBOSE && echo "$PRG: Adding DSA key to my authorized keys."
  cat $HOME/.ssh/id_dsa.pub >> $HOME/.ssh/authorized_keys
fi

# ----------------------------------------------------------------------------
# Remove keys from known_hosts
if [[ -f $HOME/.ssh/known_hosts ]]; then
  cp -p -f $HOME/.ssh/known_hosts $HOME/.ssh/known_hosts.$(date +%m%d-%H%M%S)
fi
touch $HOME/.ssh/known_hosts

for host in localhost ${LNODE} ${LNODE%%.*} ${LNODE%%.*}-priv  ${LNODE%%.*}.cluster.${LNODE#*.} ${LNODE%%.*}-priv.cluster.${LNODE#*.}
do
  echo $host
  ping $host -c 1 2> /dev/null
  if [ $? -eq 0 ]
  then
    learn_host $host
  fi
done

#learn_host localhost
#learn_host ${LNODE}
#learn_host ${LNODE%%.*}
#learn_host ${LNODE%%.*}-priv
#learn_host ${LNODE%%.*}.cluster.${LNODE#*.}
#learn_host ${LNODE%%.*}-priv.cluster.${LNODE#*.}

# ----------------------------------------------------------------------------
if $REMOTE; then
  if grep -qs -f $HOME/id_dsa.pub $HOME/.ssh/authorized_keys; then
    $VERBOSE && echo "$PRG: First node's key already exists in my authorized_keys. Not updated."
  else
    $VERBOSE && echo "$PRG: Adding first node's key to my authorized_keys"
    cat $HOME/id_dsa.pub >> $HOME/.ssh/authorized_keys
    rm -f $HOME/id_dsa.pub
  fi

  $VERBOSE && echo "$PRG: Update my known_hosts with those of first node"
  cat $HOME/.ssh/known_hosts >> $HOME/known_hosts
  sort $HOME/known_hosts | uniq > $HOME/.ssh/known_hosts
  rm -f $HOME/known_hosts
fi

# ----------------------------------------------------------------------------
# End of script
sync
if [[ ! -z ${STATFILE:-} ]]; then echo 0 > $STATFILE; fi
$VERBOSE && echo "$PRG: Done"
trap - EXIT
exit 0

