all: run

run:
	bundle exec jekyll serve -H 0.0.0.0 --trace

build:
	bundle exec jekyll build

deploy:
	git branch -D gh-pages || true
	git fetch
	bundle exec jekyll build
	cp -r _site /tmp
	git checkout gh-pages
	git pull origin gh-pages -X theirs --no-edit
	cp CNAME /tmp || true
	find . -path ./.git -prune -o \( \! -path ./.gitignore \) -exec rm -rf {} \; 2> /dev/null || true
	cp /tmp/CNAME . || true
	mv /tmp/_site/* .
	git add -A
	git commit -m "rebuilt"
	git push origin gh-pages 
	git checkout master