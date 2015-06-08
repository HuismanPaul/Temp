# ----------------------------------------------------------------------------
# Register all exitcodes and print message
#
function exitcode()
{
  # echo -n "$1: "
  case $1 in
  0)
    success
    echo
    ;;
  1)
    failure
    echo
    exit $1
    ;;
  2)
    failure
    echo
    ;;
  10)
    echo -n "$SERVICE on $NODE already started" && success
    echo
    ;;
  11)
    echo -n "$SERVICE on $NODE status" && failure
    echo
    exit $1
    ;;
  12)
    echo -n "$SERVICE on $NODE status" && success
    echo
    ;;
  20)
    echo -n "Install domain $WLDOM" && failure
    echo
    exit $1
    ;;
  21)
    echo -n "Install domain $WLDOM" && success
    echo
    ;;
  22)
    echo -n "Start domain $WLDOM" && failure
    echo
    exit $1
    ;;
  23)
    echo -n "Start domain $WLDOM" && success
    echo
    ;;
  24)
    echo -n "Stop domain $WLDOM" && failure
    echo
    exit $1
    ;;
  25)
    echo -n "Stop domain $WLDOM" && success
    echo
    ;;
  26)
    echo -n "Configure domain $WLDOM" && failure
    echo
    exit $1
    ;;
  27)
    echo -n "Configure domain $WLDOM" && success
    echo
    ;;
  28)
    echo -n "Domain $WLDOM is already started" && success
    echo
    exit $1
    ;;
  30)
    echo -n "Domain $WLDOM already enrolled" && success
    echo
    ;;
  31)
    echo -n "Enroll domain $WLDOM on $NODE" && failure
    echo
    exit $1
    ;;
  32)
    echo -n "Enroll domain $WLDOM on $NODE" && success
    echo
    ;;
  40)
    echo -n "Prerequisists failed" && failure
    echo
    exit 40
    ;;
  41)
    echo -n "Prerequisists succeeded" && success
    echo
    ;;
  42)
    echo -n "Package domain $WLDOM " && success
    echo 
    ;;
  43)
    echo -n "Package domain $WLDOM " && failure
    echo
    exit 43
    ;;
  50)
    echo -n "$NODE: Actional Agent $ACTIONAL_VERSION installed" && failure
    echo
    exit 50
    ;;
  51)
    echo -n "$NODE: Actional Agent $ACTIONAL_VERSION installed" && success
    echo
    ;;
  52)
    echo -n "$NODE: Actional Agent $ACTIONAL_VERSION already installed" && success
    echo
    ;;
  60)
    echo -n "$NODE: Actional Agent $ACTIONAL_VERSION removed" && failure
    echo
    exit 60
    ;;
  61)
    echo -n "$NODE: Actional Agent $ACTIONAL_VERSION removed" && success
    echo
    ;;
  70)
    echo -n "$NODE: Tibco Plugin $TIBCOLIB_VERSION installed" && failure
    echo
    exit 70
    ;;
  71)
    echo -n "$NODE: Tibco Plugin $TIBCOLIB_VERSION installed" && success
    echo
    ;;
  74)
    echo -n "$NODE: Tibco Plugin $TIBCOLIB_VERSION already installed" && success
   echo
    ;;
  72)
    echo -n "$NODE: Tibco Plugin $TIBCOLIB_VERSION removed" && failure
    echo
    exit 72
    ;;
  73)
    echo -n "$NODE: Tibco Plugin $TIBCOLIB_VERSION removed" && success
    echo
    ;;
  99)
    echo > /dev/null
    ;;
  esac
}

