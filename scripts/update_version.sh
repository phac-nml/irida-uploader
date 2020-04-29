# Use example:
# $./scripts/update_version.sh 0.4.2
# Use the first argument as the new version number
newversion=$1

setuppy=setup.py
sed -i "s/version=.*\,/version='$newversion',/" "$setuppy"

wininstall=windows-installer.cfg
wininstallgui=windows-gui-installer.cfg
sed -i -z "s/version=.\..\../version=$newversion/" "$wininstall"
sed -i -z "s/version=.\..\../version=$newversion/" "$wininstallgui"

clientry=iridauploader/core/cli_entry.py
sed -i "s/VERSION_NUMBER = \".\..\..\"/VERSION_NUMBER = \"$newversion\"/" "$clientry"

