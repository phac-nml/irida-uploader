#!/bin/bash

path_of_this_file=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
iu_path=$(dirname  $path_of_this_file)
make requirements
source .virtualenv/bin/activate
pycodestyle --show-source --ignore=E501 --exclude="Tests/integrationTests/repos/*",".git","bin","include","lib",\
"local" --statistics "$iu_path/api" "$iu_path/config" "$iu_path/core" \
"$iu_path/messaging" "$iu_path/model" "$iu_path/parser" "$iu_path/progress" \
"$iu_path/scripts"
deactivate
