#!/bin/bash

anaconda_dir="`pwd`"/anaconda3/
anaconda_bin="$anaconda_dir"/bin
anaconda_env_dir="$anaconda_dir"/envs

echo "Anaconda directory: $anaconda_dir"
echo "Anaconda bin directory: $anaconda_bin"
echo "Anaconda env directory: $anaconda_env_dir"

py_env_name=py35
py_env_dir="$anaconda_env_dir"/$py_env_name

echo "Python env dir: $py_env_dir"

# Ensure Anaconda 3 exists in this workspace
if [ ! -d "$anaconda_dir" ]
then
  echo "Anaconda (Python 3) not found in this workspace, installing now..."
  installer=anaconda_installer.sh
  wget https://repo.continuum.io/archive/Anaconda3-4.4.0-Linux-x86_64.sh -O $installer
  chmod +x $installer
  ./$installer -b -p "$anaconda_dir"
  rm $installer
else
  echo "Anaconda (Python 3) already exists in this workspace"
fi

# Ensure a suitable environment exists
if [ ! -d "$py_env_dir" ]
then
  echo "Python 3.5 environment not found in Anaconda directory"
  "$anaconda_bin"/conda create -y -q --override-channels -c defaults -n $py_env_name python=3.5 anaconda
else
  echo "Python 3.5 environment found"
fi

# Install Python dependencies
echo "Activating $py_env_name environment"
source "$anaconda_bin"/activate py35

echo "Installing dependencies"
"$anaconda_bin"/conda install -y -q --override-channels -c dgursoy tomopy=1.0.1
"$anaconda_bin"/conda install -y -q --override-channels -c defaults coverage flake8

echo "Anaconda directory: $anaconda_dir"
ls -la "$anaconda_dir"

echo "Anaconda env directory: $anaconda_env_dir"
ls -la "$anaconda_env_dir"
