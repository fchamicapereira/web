#!/usr/bin/env python3

import argparse
import datetime
import functools
import html
import http.server
import re
import shutil
import tomllib
import unicodedata
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"

SITE_URL = "https://fchamicapereira.me"
FIRST_NAME = "Francisco"
LAST_NAME = "Pereira"
NAME = f"{FIRST_NAME} {LAST_NAME}"
# How I appear in author lists; these names are highlighted on publications.
SELF_NAMES = {"Francisco Pereira", "F. Pereira"}
EMAIL = "francisco.chamica.pereira@tecnico.ulisboa.pt"
GITHUB_USERNAME = "fchamicapereira"
LINKEDIN_USERNAME = "fchamicapereira"
CV = "/assets/pdf/cv.pdf"

# Navbar entries shown after "about" and "cv", in order: (title, url).
NAV = [
    ("hobbies", "/hobbies/"),
    ("projects", "/projects/"),
    ("publications", "/publications/"),
    ("teaching", "/teaching/"),
]

# Link buttons shown under a publication, in order: (bib field, label, whether
# a value without "://" is a file name in public/assets/pdf/).
PAPER_BUTTONS = [
    ("html", "HTML", False),
    ("pdf", "PDF", True),
    ("supp", "Supp", True),
    ("code", "Code", False),
    ("eval", "Evaluation", False),
    ("poster", "Poster", True),
    ("slides", "Slides", True),
    ("website", "Web", False),
    ("talk", "Talk video", False),
]


def esc(text):
    return html.escape(text, quote=False)


def render(template, **values):
    """Fills the {{ name }} placeholders of templates/<template>."""
    text = (ROOT / "templates" / template).read_text()
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: values[m.group(1)], text)


# --- BibTeX -------------------------------------------------------------------


def parse_bibtex(text):
    """Parses @type{key, field = {value} or bare_word, ...} entries.

    Each entry is a dict with "type", "key" and "fields", an ordered mapping of
    field name to (raw value, whether the value was in braces).
    """
    ws = re.compile(r"\s*")
    header = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
    field_name = re.compile(r"(\w+)\s*=\s*")
    bare_value = re.compile(r"[^,}\s]+")

    entries = []
    pos = 0
    while (pos := text.find("@", pos)) != -1:
        m = header.match(text, pos)
        if not m:
            raise ValueError(f"papers.bib: bad entry header at offset {pos}")
        entry = {"type": m.group(1).lower(), "key": m.group(2), "fields": {}}
        pos = m.end()
        while True:
            pos = ws.match(text, pos).end()
            if text.startswith("}", pos):
                pos += 1
                break
            m = field_name.match(text, pos)
            if not m:
                raise ValueError(f"papers.bib: bad field in {entry['key']} at offset {pos}")
            pos = m.end()
            if text.startswith("{", pos):
                end = find_closing_brace(text, pos)
                entry["fields"][m.group(1).lower()] = (text[pos + 1 : end], True)
                pos = end + 1
            else:
                value = bare_value.match(text, pos).group()
                pos += len(value)
                entry["fields"][m.group(1).lower()] = (value, False)
            pos = ws.match(text, pos).end()
            if text.startswith(",", pos):
                pos += 1
        entries.append(entry)
    return entries


def find_closing_brace(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(f"papers.bib: unbalanced braces at offset {start}")


ACCENTS = {"`": "\u0300", "'": "\u0301", "^": "\u0302", "~": "\u0303", '"': "\u0308", "c": "\u0327"}


def latex_to_text(text):
    """Converts the LaTeX found in papers.bib (accents, dashes, quotes) to text."""
    text = re.sub(
        r"\\([`'^~\"]|c(?=\{))\{?(\w)\}?",
        lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]),
        text,
    )
    text = text.replace("{", "").replace("}", "")
    text = text.replace("---", "—").replace("--", "–").replace("~", "\u00a0")
    return text.replace("``", "“").replace("''", "”").replace("`", "‘").replace("'", "’")


def split_names(field):
    """Splits an author field into (first, last) name pairs."""
    names = []
    for name in re.split(r"\s+and\s+", field.strip()):
        if "," in name:
            last, first = (part.strip() for part in name.split(",", 1))
        else:
            first, _, last = name.strip().rpartition(" ")
        names.append((first, last))
    return names


def bibtex_html(entry):
    """The entry as BibTeX (minus its abstract), marked up the way Rouge does
    so the Pygments highlight themes apply."""

    def span(cls, text):
        return f'<span class="{cls}">{esc(text)}</span>'

    fields = []
    for name, (value, braced) in entry["fields"].items():
        if name == "abstract":
            continue
        if name == "author":
            value = " and ".join(f"{last}, {first}" for first, last in split_names(value))
        value = span("s", "{" + value + "}") if braced else span("nv", value)
        fields.append(f"  {span('na', name)} {span('p', '=')} {value}")
    code = "\n".join([
        span("nc", "@" + entry["type"]) + span("p", "{") + span("nl", entry["key"]) + span("p", ","),
        (span("p", ",") + "\n").join(fields),
        span("p", "}"),
    ])
    return f'<figure class="highlight"><pre><code class="language-bibtex" data-lang="bibtex">{code}</code></pre></figure>'


def authors_html(field, coauthors):
    parts = []
    for first, last in split_names(field):
        name = latex_to_text(f"{first} {last}".strip())
        if name in SELF_NAMES:
            parts.append(f"<b><em>{esc(name)}</em></b>")
        elif name in coauthors:
            parts.append(f'<a href="{html.escape(coauthors[name])}">{esc(name)}</a>')
        else:
            parts.append(esc(name))
    if len(parts) == 1:
        return parts[0]
    return ",\u00a0".join(parts[:-1]) + ",\u00a0and " + parts[-1]


def paper_html(entry, coauthors):
    fields = {name: value for name, (value, _) in entry["fields"].items()}
    bibtex_show = fields.get("bibtex_show", "").strip().lower() == "true"

    links = []
    if "abstract" in fields:
        links.append('<a class="abstract btn btn-sm z-depth-0" role="button">Abs</a>')
    if "arxiv" in fields:
        links.append(f'<a href="http://arxiv.org/abs/{html.escape(fields["arxiv"])}" target="_blank" class="btn btn-sm z-depth-0" role="button">arXiv</a>')
    if bibtex_show:
        links.append('<a class="bibtex btn btn-sm z-depth-0" role="button">Bib</a>')
    for field, label, is_pdf in PAPER_BUTTONS:
        if field in fields:
            url = fields[field]
            if is_pdf and "://" not in url:
                url = "/assets/pdf/" + urllib.parse.quote(url)
            links.append(f'<a href="{html.escape(url)}" target="_blank" class="btn btn-sm z-depth-0" role="button">{label}</a>')

    hidden = []
    if "abstract" in fields:
        hidden.append(f'<div class="abstract hidden">\n<p>{esc(latex_to_text(fields["abstract"]))}</p>\n</div>')
    if bibtex_show:
        hidden.append(f'<div class="bibtex hidden">\n{bibtex_html(entry)}\n</div>')

    badge = ""
    if "abbr" in fields:
        slug = re.sub(r"[^a-z0-9]+", "-", fields["abbr"].lower()).strip("-")
        badge = f'<abbr class="badge badge-{slug}">{esc(fields["abbr"])}</abbr>'

    return f"""<li>
<div class="row">
  <div class="col-sm-2 abbr">{badge}</div>
  <div id="{entry['key']}" class="col-sm-8">
    <div class="title">{esc(latex_to_text(fields.get('title', '')))}</div>
    <div class="author">{authors_html(fields.get('author', ''), coauthors)}</div>
    <div class="periodical">{esc(latex_to_text(fields.get('label', '')))}</div>
    <div class="links">
      {chr(10).join(links)}
    </div>
    {chr(10).join(hidden)}
  </div>
</div>
</li>"""


def bibliography_html(entries, coauthors):
    items = "\n".join(paper_html(entry, coauthors) for entry in entries)
    return f'<ol class="bibliography">\n{items}\n</ol>'


# --- Other page pieces --------------------------------------------------------


def projects_html():
    projects = tomllib.loads((ROOT / "data" / "projects.toml").read_text())["project"]
    out = ['<div class="projects">']
    for category in dict.fromkeys(p["category"] for p in projects):
        out.append(f'<h2 class="category">{esc(category)}</h2>')
        out.append('<div class="grid">')
        for p in projects:
            if p["category"] != category:
                continue
            github = ""
            if "github" in p:
                github = f"""<div class="github-icon">
              <div class="icon" data-toggle="tooltip" title="Code Repository">
                <a href="{html.escape(p['github'])}"><i class="fab fa-github gh-icon"></i></a>
              </div>
            </div>"""
            out.append(f"""<div class="grid-sizer"></div>
<div class="grid-item">
  <a href="{html.escape(p['url'])}">
    <div class="card hoverable">
      <div class="card-body">
        <h2 class="card-title">{esc(p['title'])}</h2>
        <p class="card-text">{esc(p['description'])}</p>
        <div class="row ml-1 mr-1 p-0">
          {github}
        </div>
      </div>
    </div>
  </a>
</div>""")
        out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


def social_html():
    # Percent-encode the address so naive scrapers don't pick it up.
    email = "".join(c if c in ".@" else f"%{ord(c):02X}" for c in EMAIL)
    return " ".join([
        f'<a href="mailto:{email}" title="email"><i class="fas fa-envelope"></i></a>',
        f'<a href="https://github.com/{GITHUB_USERNAME}" title="GitHub"><i class="fab fa-github"></i></a>',
        f'<a href="https://www.linkedin.com/in/{LINKEDIN_USERNAME}" title="LinkedIn"><i class="fab fa-linkedin"></i></a>',
    ])


def nav_html(active):
    items = [("about", "/", False), ("cv", CV, True)] + [(title, url, False) for title, url in NAV]
    out = []
    for title, url, new_tab in items:
        target = ' target="_blank"' if new_tab else ""
        if title == active:
            out.append(f'<li class="nav-item active"><a class="nav-link" href="{url}"{target}>{title}<span class="sr-only">(current)</span></a></li>')
        else:
            out.append(f'<li class="nav-item"><a class="nav-link" href="{url}"{target}>{title}</a></li>')
    return "\n".join(out)


def open_external_links_in_new_tab(page):
    """Adds target="_blank" and rel="noopener noreferrer" to links leaving the site."""
    site_host = urllib.parse.urlparse(SITE_URL).hostname

    def fix(m):
        tag = m.group(0)
        href = re.search(r'href="(https?://[^"]*)"', tag)
        if not href or urllib.parse.urlparse(html.unescape(href.group(1))).hostname == site_host:
            return tag
        if "target=" not in tag:
            tag = tag[:-1] + ' target="_blank">'
        if "rel=" not in tag:
            tag = tag[:-1] + ' rel="noopener noreferrer">'
        return tag

    return re.sub(r"<a\s[^>]*>", fix, page)


def write_page(path, url, *, title, content, active=None, description="", head_extra=""):
    today = datetime.date.today()
    brand = ""
    if url != "/":
        brand = f'<a class="navbar-brand title font-weight-lighter" href="{SITE_URL}/"><span class="font-weight-bold">{FIRST_NAME}</span> {LAST_NAME}</a>'
    page = render(
        "base.html",
        head_extra=head_extra,
        title=f"{NAME} | {title}" if title else NAME,
        name=NAME,
        description=html.escape(description),
        canonical=SITE_URL + url,
        brand=brand,
        nav=nav_html(active),
        content=content,
        year=str(today.year),
        updated=f"{today:%B} {today.day}, {today.year}",
    )
    out = OUT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(open_external_links_in_new_tab(page))


def write_basic_page(path, url, title, content, *, active=None, description="", head_extra=""):
    """A page with a heading and optional description above its content."""
    content = render("page.html", heading=title[:1].upper() + title[1:], description=esc(description), content=content)
    write_page(path, url, title=title, content=content, active=active, description=description, head_extra=head_extra)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "public", OUT)
    # Serve the files as they are; don't let GitHub Pages run Jekyll on them.
    (OUT / ".nojekyll").touch()

    papers = parse_bibtex((ROOT / "data" / "papers.bib").read_text())
    coauthors = tomllib.loads((ROOT / "data" / "coauthors.toml").read_text())
    selected = [p for p in papers if p["fields"].get("selected", ("",))[0].strip().lower() == "true"]

    about = render(
        "about.html",
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
        social=social_html(),
        content=(ROOT / "pages" / "about.html").read_text(),
        selected_papers=bibliography_html(selected, coauthors),
    )
    write_page("index.html", "/", title="", content=about, active="about")

    publications = f'<div class="publications">\n{bibliography_html(papers, coauthors)}\n</div>'
    write_basic_page("publications/index.html", "/publications/", "publications", publications, active="publications")
    write_basic_page("projects/index.html", "/projects/", "projects", projects_html(), active="projects")
    for name in ("hobbies", "teaching"):
        content = (ROOT / "pages" / f"{name}.html").read_text()
        write_basic_page(f"{name}/index.html", f"/{name}/", name, content, active=name)

    write_basic_page(
        "404.html",
        "/404.html",
        "Page not found",
        (ROOT / "pages" / "404.html").read_text(),
        description="Looks like there has been a mistake. Nothing exists here.",
        head_extra=f'<meta http-equiv="refresh" content="3; url={SITE_URL}/" />',
    )

    urls = "\n".join(f"<url><loc>{SITE_URL}{url}</loc></url>" for url in ["/"] + [url for _, url in NAV])
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n'
    )


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """Makes browsers recheck files on every request, so previews are never stale."""

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(
        description="Build the website into _site/. Files in public/ are copied as-is; "
        "pages are assembled from templates/, pages/ and data/.",
        epilog="examples:\n"
        "  ./build.py          build into _site/\n"
        "  ./build.py --serve  build, then preview on http://localhost:8000",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--serve", action="store_true", help="serve _site/ locally after building")
    parser.add_argument("--port", type=int, default=8000, help="port for --serve (default: %(default)s)")
    args = parser.parse_args()

    build()
    print(f"Built {OUT.relative_to(ROOT)}/")
    if args.serve:
        handler = functools.partial(NoCacheHandler, directory=OUT)
        with http.server.ThreadingHTTPServer(("localhost", args.port), handler) as server:
            print(f"Serving on http://localhost:{args.port} (Ctrl+C to stop)")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nStopped.")


if __name__ == "__main__":
    main()
