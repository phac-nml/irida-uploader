#!/usr/bin/env bash
# This script updates the version number in the various locations they need to be changed including:
#   setup.py : for pypi / pip
#   windows-installer.cfg: for pynsist windows builds
#   cli_entry.py : for version identifiers in the main code base
# Use example:
# $./scripts/update_version.sh 0.4.2
# Use the first argument as the new version number
newversion=$1

setuppy=setup.py
sed -i "s/version=.*\,/version='$newversion',/" "$setuppy"

wininstall=windows-installer.cfg
sed -i -z "s/version=.\..\../version=$newversion/" "$wininstall"

clientry=iridauploader/core/cli_entry.py
sed -i "s/VERSION_NUMBER = \".\..\..\"/VERSION_NUMBER = \"$newversion\"/" "$clientry"

