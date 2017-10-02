#!/bin/bash

anaconda_dir="`pwd`"/anaconda2/
anaconda_bin="$anaconda_dir"/bin
anaconda_env_dir="$anaconda_dir"/envs

echo "Anaconda directory: $anaconda_dir"
echo "Anaconda bin directory: $anaconda_bin"
echo "Anaconda env directory: $anaconda_env_dir"

# Ensure Anaconda 2 exists in this workspace
if [ ! -d "$anaconda_dir" ]
then
  echo "Anaconda (Python 2) not found in this workspace, installing now..."
  installer=anaconda_installer.sh
  wget https://repo.continuum.io/archive/Anaconda2-4.4.0-Linux-x86_64.sh -O $installer
  chmod +x $installer
  ./$installer -b -p "$anaconda_dir"
  rm $installer
else
  echo "Anaconda (Python 2) already exists in this workspace"
fi

# Install Python dependencies
echo "Installing dependencies"
"$anaconda_bin"/conda install -y -q --override-channels -c dgursoy tomopy=1.0.1
"$anaconda_bin"/conda install -y -q --override-channels -c defaults mock

echo "Anaconda directory: $anaconda_dir"
ls -la "$anaconda_dir"
