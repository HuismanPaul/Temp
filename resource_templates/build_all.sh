#!/bin/bash
#
# SCRIPT
#   build_all.sh
# DESCRIPTION
#   This script enters the subtree and finds the build.sh
#   files to execute them. This way all RPM's are built.
# ARGUMENTS
#   None.
# RETURN
#   0: success.
# DEPENDENCIES
# FAILURE
# AUTHORS
#   Date strings made with 'date +"\%Y-\%m-\%d \%H:\%M"'.
#   Allard Berends (AB), 2014-08-15 16:15
# HISTORY
# LICENSE
#   Copyright (C) 2014 Allard Berends
# 
#   build_all.sh is free software; you can redistribute it
#   and/or modify it under the terms of the GNU General
#   Public License as published by the Free Software
#   Foundation; either version 3 of the License, or (at your
#   option) any later version.
#
#   build_all.sh is distributed in the hope that it will be
#   useful, but WITHOUT ANY WARRANTY; without even the
#   implied warranty of MERCHANTABILITY or FITNESS FOR A
#   PARTICULAR PURPOSE. See the GNU General Public License
#   for more details.
#
#   You should have received a copy of the GNU General
#   Public License along with this program; if not, write to
#   the Free Software Foundation, Inc., 59 Temple Place -
#   Suite 330, Boston, MA 02111-1307, USA.
# DESIGN
#

PNAME=$(basename $0)
OPWD=$(pwd)
cd $(dirname $0)
CWD=$(pwd)

BUILD_FILES=$(find . -name 'build.sh')
for i in $BUILD_FILES
do
  cd $(dirname $i)
  RPM=$(sed -n 's/^RPM=//p' build.sh)
  echo $RPM
  ./build.sh >/dev/null 2>&1 || echo "$PNAME: ERROR: $i did not build" >&2
  cd $CWD
done

cd $OPWD
