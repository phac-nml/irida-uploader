#!/usr/bin/env bash

if [[ $1 == unit ]]; then
    python3 -m unittest discover -s tests -t .
elif [[ $1 == integration_master ]]; then
    xvfb-run --auto-servernum --server-num=1 python3 start_integration_tests.py
elif [[ $1 == integration_dev ]]; then
        xvfb-run --auto-servernum --server-num=1 python3 start_integration_tests_dev.py
else
    exit 1
fi
