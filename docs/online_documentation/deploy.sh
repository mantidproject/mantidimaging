#!/bin/bash

cd ./build/html/
git init

git add .
git commit -m "Deploy documentation"

git push --force git@github.com:mantidproject/mantidimaging.git master:gh-pages

# Or for non-interactive deployment
# git push --force --quiet "https://${GH_TOKEN}@${GH_REF}" master:gh-pages > /dev/null 2>&1
