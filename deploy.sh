#!/bin/bash

set -eou pipefail

bundle exec jekyll build
cp -r _site /tmp
git checkout gh-pages
git pull origin gh-pages
mv /tmp/_site/* .
git add -A
git commit -m "rebuilt"
git push origin gh-pages 
git checkout master
