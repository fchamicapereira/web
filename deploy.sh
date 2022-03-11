#!/bin/bash

set -eoxu pipefail

bundle exec jekyll build
cp -r _site /tmp
git checkout gh-pages
git pull -X theirs --no-edit
cp CNAME /tmp
find . -path ./.git -prune -o \( \! -path ./.gitignore \) -exec rm -rf {} \; 2> /dev/null || true
cp /tmp/CNAME .
mv /tmp/_site/* .
git add -A
git commit -m "rebuilt"
git push origin gh-pages 
git checkout master
