#!/bin/bash

# This file is modified from https://irida.corefacility.ca/gitlab/irida/import-tool-for-galaxy/blob/development/irida_import/tests/integration/bash_scripts/install.sh

if ! mkdir repos
then
    echo >&2 "Removing repos directory"
    rm -rf repos
    mkdir repos
fi
pushd repos

echo "Downloading IRIDA..."
if ! git clone https://github.com/phac-nml/irida.git
then
    echo >&2 "Failed to clone"
    exit 1
else
  pushd irida
  git checkout $1
  git fetch
  git reset --hard
  git clean -fd
  git pull
  echo "Preparing IRIDA for first excecution..."

  pushd lib
  ./install-libs.sh
  popd
  popd
  echo "IRIDA has been installed"
fi

