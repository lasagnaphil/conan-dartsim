#!/bin/bash

set -e
set -x

python --version

if [[ "$(uname -s)" == 'Darwin' ]]; then
    pyenv activate conan
fi

python build.py
