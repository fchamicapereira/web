# Personal webpage

Source of [fchamicapereira.me](https://fchamicapereira.me): a movie theatre's programme playing on an old CRT at 3am. The site is plain HTML/CSS/JS, assembled by `build.py`, which only needs Python 3.11+ (standard library only).

## Usage

```sh
./build.py           # build into _site/
./build.py --serve   # build, then preview on http://localhost:8000
./build.py --help    # all options
```

Pushing to `master` builds the site and publishes it to the `gh-pages` branch, which GitHub Pages serves (`.github/workflows/deploy.yml`).

## Layout

| Path                  | Contents                                                                    |
| --------------------- | --------------------------------------------------------------------------- |
| `build.py`            | Build script; also holds site settings (name, email, tagline, menu order).  |
| `templates/`          | Page layouts with `{{ placeholder }}` slots.                                |
| `pages/`              | Page text (HTML): about, the hobbies intro, the 404 page.                   |
| `pages/posts/`        | The text of each blog post on `/hobbies/`.                                  |
| `data/papers.bib`     | Publications, shown on `/publications/` and, if selected, on the home page. |
| `data/coauthors.toml` | Coauthor homepages, linked from author lists.                               |
| `data/projects.toml`  | Project posters on `/projects/`.                                            |
| `data/teaching.toml`  | Ticket stubs on `/teaching/`.                                               |
| `data/posts.toml`     | Blog posts on `/hobbies/`: slug, topic, title, excerpt, optional date.      |
| `data/news.toml`      | News on the home page: date and text; the newest five are shown.            |
| `public/`             | Files copied as-is: `site.css`, `site.js`, fonts, images, PDFs (including the CV), `CNAME`. |

## Adding a publication

Add an entry to `data/papers.bib`. Fields the site uses besides the usual ones:

- `label`: venue shown under the authors, e.g. `{NSDI '24}`.
- `abbr`: shown as a tag next to the venue unless it is `{article}`, e.g. `{poster}`.
- `selected = {true}`: also list it under "Recent publications" on the home page.
- `bibtex_show = {true}`: show the "BibTeX" button.
- `pdf`, `slides`, `poster`, `supp`: a file name in `public/assets/pdf/` or a full URL.
- `code`, `eval`, `website`, `talk`, `html`, `arxiv`: links shown as buttons.

## Adding a blog post

Add an entry at the top of `data/posts.toml` and write its text in `pages/posts/<slug>.html`. The post appears at `/hobbies/<slug>/`.
