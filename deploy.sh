#!/bin/bash

set -eou pipefail

bundle exec jekyll build
cp -r _site /tmp
git checkout gh-pages
git pull origin gh-pages
find . -path ./.git -prune -o -exec rm -rf {} \; 2> /dev/null || true
mv /tmp/_site/* .
git add -A
git commit -m "rebuilt"
git push origin gh-pages 
git checkout master
