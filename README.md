# Personal webpage

Source of [fchamicapereira.me](https://fchamicapereira.me). The site is plain HTML/CSS/JS, assembled by `build.py`, which only needs Python 3.11+ (standard library only). The styling comes from the [al-folio](https://github.com/alshedivat/al-folio) theme.

## Usage

```sh
./build.py           # build into _site/
./build.py --serve   # build, then preview on http://localhost:8000
./build.py --help    # all options
```

Pushing to `master` builds the site and publishes it to the `gh-pages` branch, which GitHub Pages serves (`.github/workflows/deploy.yml`).

## Layout

| Path                  | Contents                                                              |
| --------------------- | --------------------------------------------------------------------- |
| `build.py`            | Build script; also holds site settings (name, email, navbar order).   |
| `templates/`          | Page layouts with `{{ placeholder }}` slots.                          |
| `pages/`              | Page content (HTML) for about, hobbies, teaching and 404.             |
| `data/papers.bib`     | Publications, shown on `/publications/` and, if selected, on the home page. |
| `data/coauthors.toml` | Coauthor homepages, linked from author lists.                         |
| `data/projects.toml`  | Project cards on `/projects/`.                                        |
| `public/`             | Files copied as-is: CSS, JS, images, PDFs (including the CV), `CNAME`. |

## Adding a publication

Add an entry to `data/papers.bib`. Fields the site uses besides the usual ones:

- `label`: venue shown under the authors, e.g. `{NSDI '24}`.
- `abbr`: badge on the left, e.g. `{article}` or `{poster}`.
- `selected = {true}`: also list it under "Recent publications" on the home page.
- `bibtex_show = {true}`: show the "Bib" button.
- `pdf`, `slides`, `poster`, `supp`: a file name in `public/assets/pdf/` or a full URL.
- `code`, `eval`, `website`, `talk`, `html`, `arxiv`: links shown as buttons.
