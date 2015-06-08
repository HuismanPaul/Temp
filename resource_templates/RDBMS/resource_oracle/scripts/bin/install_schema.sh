#!/bin/bash
#
# SCRIPT
#	install_schema
#
# SYNOPSIS
#
# DESCRIPTION
#	Create schema's as defined in the property file
#
# ARGUMENTS
#	<file> - file containing the schemas to create
#
# NOTES
# 	exisiting schemas in the database are left alone, they are not recreated
#
#	The file must contain the following format :
#	  SCHEMA_NAME=NAME:INIT_SIZE:EXTEND_SIZE:MAX_SIZE
# 	Where :
#	  NAME              = the base name to use for the derived schemas
#	  INITIAL_SIZE      = the initial size of the named tabelspace
#	  EXTEND_SIZE       = the size of the extents
#	  MAX_SIZE	    = the maximum size a tablespace can grow to.
#
# DEPENDENCIES
#
# RETURN
#
# CHANGELOG
#	Date:      By:              Action:
#	---------- ---------------- -----------------------------------
#	21-05-2015 Ed Groenenberg   Create
#
#

PRG=$(basename $0 .sh)

#-----------------------------------------------------------------------------
# Must run as root.
#
[ "$(id -un)" != "root"  ] && echo >&2 "$PRG: must be run as root" && exit 1

#-----------------------------------------------------------------------------
# Default settings
#
function Defaults()
{
  DB_OWNER=oracle
  TS_DINI=100 		# default minimal user tablespace size in Mb
  TS_DEXT=100		# default next extend size in Mb
  TS_DMAX=9216		# default maximum user tablespace size in Mb
  TS_TMAX=5192		# default maximum temp TS size in Mb
}

# ----------------------------------------------------------------------------
# SETUP_ENV : Settings & pre-checks
#
function Setup_Env()
{
  [ ! -f /etc/oratab ] && echo -e "\n/etc/oratab file bestaat niet.\n" && exit 1

  A=$(grep db_1 /etc/oratab | grep -v '^#')
  [ -z "$A" ] && echo -e "\nGeen database info in /etc/oratab.\n" && exit 1

  ORACLE_SID=$(echo $A | awk -F: '{print $1}')
  if [ -z $ORACLE_SID ] || [ "$ORACLE_SID" = "*" ]; then
    echo -e "\nGeen valide SID entry in /etc/oratab.\n"
    exit 1
  fi

  B=${ORACLE_SID:${#ORACLE_SID}-1:1}		# HB or VB mode?
  if [ $B = 1 -o $B = 2 ]; then
    DB_NAME=${ORACLE_SID:0:${#ORACLE_SID}-1}
    RAC_MODE=1
  else
    DB_NAME=$ORACLE_SID
    RAC_MODE=0
  fi

  ORACLE_HOME=$(echo $A | awk -F: '{print $2}')
  if [ -z $ORACLE_HOME ] || [ ! -d $ORACLE_HOME ]; then
    echo -e "\nGeen oracle directory entry in /etc/oratab.\n"
    exit 1
  fi

  MACHINE_DOMAIN=$(dnsdomainname)
  [ -z $MACHINE_DOMAIN ] && echo -e "\nSysteem domainnaam is niet ingesteld.\n" && exit 1

  INSTALLDIR=/opt/oracle/admin/$DB_NAME
  INSTALLSCRIPTS=$INSTALLDIR/scripts
  INSTALLLOG=$INSTALLSCRIPTS/log

  trap "Clean_Up; exit 1" INT TERM EXIT HUP QUIT
}

# ----------------------------------------------------------------------------
# CLEAN_UP : Cleanup possible leftovers.
#
function Clean_Up()
{
  trap - EXIT
}

# ----------------------------------------------------------------------------
# Usage : A minimal help
#
function Usage()
{
  cat <<-EOF

Usage: $PRG <schema definitions file>

EOF
exit 1
}

#----------------------------------------------------------------------------
# $1 -> schema definition list file
#
function Process_Schema_List()
{
  SCHEMA_LIST=$(grep '^SCHEMA_USER=' $1 | awk -F# '{print $1}' | awk -F= '/SCHEMA_USER/ {print $2}')

  for SCHEMA in $SCHEMA_LIST; do
    TS_USR=$(echo $SCHEMA | awk -F: '{print $1}')

    TS_INI=$(echo $SCHEMA | awk -F: '{print $2}')
    [ -z $TS_INI ] && TS_INI=$TS_DINI
    [ $TS_INI -ge $TS_DMAX ] && TS_INI=$(($TS_INI-1024))

    TS_EXT=$(echo $SCHEMA | awk -F: '{print $3}')
    [ -z $TS_EXT ] && TS_EXT=$TS_DEXT
    [ $TS_EXT -ge $TS_DEXT ] && TS_EXT=$TS_DEXT

    TS_MAX=$(echo $SCHEMA | awk -F: '{print $4}')
    [ -z $TS_MAX ] && TS_MAX=0
    [ $TS_MAX -ge $TS_DMAX ] && TS_MAX=$TS_DMAX

    Check_Schema $TS_USR
    if [ $? -eq 0 ]; then 
      Create_Schema $TS_USR $TS_INI $TS_EXT $TS_MAX
      [ $? -ne 0 ] && return 1
    else
      printf "Schema '%-15s' bestaat al, geen verdere actie nodig.\n" $TS_USR
    fi
  done
  return 0
}

#----------------------------------------------------------------------------
# Check is a schema already exists. If so skip it.
#
function Check_Schema()
{
  R=$(su - $DB_OWNER -c "
	export ORAENV_ASK=NO
	export ORACLE_SID=$ORACLE_SID
	. oraenv 2>&1 >/dev/null
	$ORACLE_HOME/bin/sqlplus -s /nolog <<EOS
		connect / as sysdba
		set heading off feedback off pagesize 0
		select count(*) from all_users where username = upper('$1');
		exit
		EOS
	")

  if (( $? > 0 )) || (( R != 0 && R != 1 )); then
    echo -e "\nFout opgetreden : ${R}.\n"
    exit 1
  fi

  return $R
}

#-----------------------------------------------------------------------------
# Create the standard schema for a given username
# $1 - Username
# $2 - Initial tablespace size
# $3 - extent size
# $4 - Maximum size
#
function Create_Schema()
{
  F_USER=$(echo $1 | tr [:lower:] [:upper:])	# full name in upper case
  S_USER=$(echo ${F_USER%_OWNER*})		# short name
  SERVICE="${S_USER}_${DB_NAME}.${MACHINE_DOMAIN}"
  SQLFILE=$INSTALLSCRIPTS/create_${S_USER}.sql

  rm -f $SQLFILE

  cat <<-EOF > $SQLFILE
	set echo on verify off
	connect / as sysdba
	whenever sqlerror exit

	spool $INSTALLSCRIPTS/create_${S_USER}.lis

	create	smallfile tablespace ${F_USER}_DATA logging 
		datafile size ${2}M autoextend on next ${3}M
		maxsize ${4}M extent management local
		segment space management auto;

	create	user ${F_USER}
		temporary tablespace temp
		default tablespace ${F_USER}_DATA
		identified by ${S_USER}
		quota unlimited on ${F_USER}_DATA;

	grant	create session,
		create cluster,
		create indextype,
		create job,
		create materialized view,
		create procedure,
		create sequence,
		create synonym,
		create table,
		create trigger,
		create type,
		create view,
		query rewrite,
		select_catalog_role
		to ${F_USER};

	grant	read, write on directory dump to ${F_USER};

	create	temporary tablespace TEMP_${F_USER}_B
		tempfile size ${2}M
		autoextend on next ${3}M
		maxsize 5120M;

	create	user ${F_USER}_BATCH
		temporary tablespace TEMP_${F_USER}_B
		default tablespace ${F_USER}_DATA
		identified by ${S_USER}
		quota unlimited on ${F_USER}_DATA;

	create	user ${F_USER}_KIJK
		default tablespace ${F_USER}_DATA
		temporary tablespace TEMP
		identified by ${S_USER}
		quota unlimited on ${F_USER}_DATA
		account unlock;

	create	role ${F_USER}_BATCH_ROLE;
	create	role ${F_USER}_KIJK_ROLE;
	create	role ${F_USER}_ADMIN_ROLE;
	create	role ${F_USER}_OWNER_ROLE;

	grant	create session,
		create synonym
		to ${F_USER}_KIJK_ROLE;

	grant	select_catalog_role to ${F_USER}_ADMIN_ROLE;

	grant	create session,
		create cluster,
		create indextype,
		create job,
		create materialized view,
		create procedure,
		create sequence,
		create synonym,
		create table,
		create trigger,
		create type,
		create view,
		query rewrite,
		select_catalog_role
		to ${F_USER}_BATCH_ROLE;

	grant	${F_USER}_BATCH_ROLE to ${F_USER}_BATCH;

	grant	${F_USER}_KIJK_ROLE to ${F_USER}_KIJK;

	grant	${F_USER}_KIJK_ROLE,
		${F_USER}_OWNER_ROLE,
		${F_USER}_BATCH_ROLE
		to ${F_USER}_ADMIN_ROLE;

	exec	dbms_service.create_service('${SERVICE}','${SERVICE}');
	exec	dbms_service.start_service('${SERVICE}', dbms_service.all_instances);

	EOF

  if [ $RAC_MODE -eq 1 ]; then
    cat <<-EOF >> $SQLFILE
	host srvctl add service -d ${DB_NAME} -s ${SERVICE} -r ${DB_NAME}1,${DB_NAME}2
	host srvctl start service -d ${DB_NAME} -s ${SERVICE}

	EOF
  fi

  cat <<-EOF >> $SQLFILE
	spool off
	exit
	EOF

  printf "Schema '%-20s' en afgeleiden ervan niet aanwezig, wordt aangemaakt.\n" ${F_USER}
  su - $DB_OWNER -c "
	export ORAENV_ASK=NO
	export ORACLE_SID=$ORACLE_SID
	. oraenv 2>&1 >/dev/null
	sqlplus /nolog @$SQLFILE
	" 2>&1 >/dev/null
}

#
# ----- MAIN ------------------------------------------------------------------
#

Setup_Env

[ -z $1 ] && Usage
[ ! -f $1 ] && echo -e "\nFile '$1' niet gevonden of leesbaar.\n" && exit 1

Defaults
echo
Process_Schema_List $1
[ $? -ne 0 ] && echo "Fout opgetreden."
echo

Clean_Up
#
