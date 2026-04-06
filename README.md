# Personal webpage

This is my personal webpage, powered by [Jekyll](https://jekyllrb.com/) (Ruby on Rails) and forked from [al-folio](https://github.com/alshedivat/al-folio).

## Setup

- Option 1: run natively
  - [Install Jekyll](https://jekyllrb.com/docs/installation/)
- Option 2: run on a container
  - [Install docker](https://docs.docker.com/engine/install/)

## Operations

|        | Native        | Docker        |
| ------ | ------------- | ------------- |
| Run    | `make run`    | `./run.sh`    |
| Deploy | `make deploy` | `./deploy.sh` |

**Note:** the deploy operation was built to work for [GitHub Pages](https://pages.github.com/). Nevertheless, as it builds the final static product of the site, it should be useful to other services.

## Site structure

| Page         | URL               | In Nav |
| ------------ | ----------------- | ------ |
| About        | `/`               | yes    |
| Publications | `/publications/`  | yes    |
| Teaching     | `/teaching/`      | yes    |
| Hobbies      | `/hobbies/`       | yes    |
| Projects     | `/projects/`      | no     |
| Fun          | `/fun/`           | no     |

## Navigating the project

| Directory/Folder           | Description                                                        |
| -------------------------- | ------------------------------------------------------------------ |
| `_config.yml`              | Generic webpage configuration.                                     |
| `assets`                   | Static assets for public access (*e.g.* CV, papers, images).       |
| `_bibliography/papers.bib` | Publication bibliography.                                          |
| `_pages`                   | Markdown pages (one per site page listed above).                   |
| `_layouts`                 | HTML layouts for each page.                                        |
| `_includes`                | Reusable HTML partials included by layouts.                        |
| `_projects`                | Markdown entries for individual project cards.                     |
| `_fun`                     | Markdown entries for individual fun project cards.                 |
| `_data`                    | YAML data files (*e.g.* co-author metadata).                       |
| `_sass`                    | SASS stylesheets.                                                  |
| `_plugins`                 | Custom Jekyll plugins.                                             |
| `_site`                    | Final statically generated built site (`bundle exec jekyll build`) |

## Adding a new page

1. Create a new file inside `_pages` (or adapt from an already existing one).
2. Configure the file to use a custom layout under `_layouts` (or use an existing one).
3. Set `nav: true` for it to be visible and accessible on the header.
4. Fill in the HTML content on the markdown file.

## Adding a new publication

1. Add a new entry to `_bibliography/paper.bib`.
2. Set its `selected` bib field to `true` if you want it to show on the home page.
3. If this is the first paper from a new year, add the year to the `years` list on `_pages/publications.md`.