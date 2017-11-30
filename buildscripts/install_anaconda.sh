#!/bin/bash

anaconda_url="https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

anaconda_dir="`pwd`"/anaconda/
anaconda_bin="$anaconda_dir"/bin
anaconda_install_args=""

while getopts ":b" o; do
  case "${o}" in
    b)
      anaconda_install_args="-b"
      ;;
  esac
done

echo "Anaconda directory: $anaconda_dir"
echo "Anaconda bin directory: $anaconda_bin"
echo "Anaconda installer arguments: $anaconda_install_args"

# Ensure Anaconda exists in this workspace
if [ ! -d "$anaconda_dir" ]
then
  echo "Anaconda (Python 3) not found in this workspace, installing now..."
  installer=anaconda_installer.sh
  wget $anaconda_url -O $installer
  chmod +x $installer
  ./$installer -p "$anaconda_dir" "$anaconda_install_args"
  rm $installer
else
  echo "Anaconda already exists in this workspace"
fi

echo "Anaconda directory: $anaconda_dir"
ls -la "$anaconda_dir"
