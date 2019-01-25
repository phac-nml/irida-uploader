#!/bin/bash
path_of_this_file=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
iu_path=$(dirname  $path_of_this_file)
find "$iu_path/Tests/" -type f -name '.miseqUploaderComplete' -print0 |xargs -0 rm
