#!/bin/bash

set -e
set -x

pip install conan --upgrade
pip install conan_package_tools

conan user

conan remote add rhol https://api.bintray.com/conan/rhololkeolke/public-conan
conan remote add bincrafters https://api.bintray.com/conan/bincrafters/public-conan
conan remote add conan-community https://api.bintray.com/conan/conan-community/conan
