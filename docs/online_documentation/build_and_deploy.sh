#!/bin/bash

# Make sure the documentation is built
make clean
make html

# Create a Git repo in the built HTML
cd ./build/html/
git init

# Commit it all
git add .
git commit -m "Deploy documentation"

# Force push it to GH pages
git push --force git@github.com:mantidproject/mantidimaging.git master:gh-pages

# Or for non-interactive deployment
# git push --force --quiet "https://${GH_TOKEN}@${GH_REF}" master:gh-pages > /dev/null 2>&1
