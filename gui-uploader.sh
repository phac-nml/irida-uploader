#!/usr/bin/env bash
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


source ${ROOT_DIR}/.virtualenv/bin/activate

if [[ $? -eq 0 ]]; then
    true
else
    echo "Failed to start Uploader Environment. Please run 'make' before running this script"
    exit 1
fi

python upload_gui.py
