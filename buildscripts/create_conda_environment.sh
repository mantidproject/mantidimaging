#!/bin/bash

anaconda_dir="`pwd`"/anaconda/

env_file=$1
env_name=$2

env_dir=${anaconda_dir}/envs/${env_name}

# Check if the environment already exists
if [ ! -d "$env_dir" ]
then
  # Create the environment
  echo "Creating environment ${env_name}..."
  ${anaconda_dir}/bin/conda env create -n ${env_name} -f ${env_file}
else
  echo "Environment ${env_name} already exists"
fi

echo "Environment directory: ${env_dir}"
ls -la ${env_dir}
