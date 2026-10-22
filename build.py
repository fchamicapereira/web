#!/usr/bin/env python3

import argparse
import datetime
import functools
import html
import http.server
import random
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

# The marquee's second line, and the line under it.
MARQUEE_SUBTITLE = "Now showing · Systems & Networking"
TAGLINE = "PhD student in systems and networking at Instituto Superior Técnico, with a Carnegie Mellon affiliation. Researcher at INESC-ID."

# Menu entries shown after "about" and "cv", in order: (title, url).
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


def load_toml(name):
    return tomllib.loads((ROOT / "data" / name).read_text())


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


def bibtex_text(entry):
    """The entry as BibTeX, minus its abstract, with authors as "Last, First"."""
    fields = []
    for name, (value, braced) in entry["fields"].items():
        if name == "abstract":
            continue
        if name == "author":
            value = " and ".join(f"{last}, {first}" for first, last in split_names(value))
        fields.append(f"  {name} = {{{value}}}" if braced else f"  {name} = {value}")
    return f"@{entry['type']}{{{entry['key']},\n" + ",\n".join(fields) + "\n}"


def authors_html(field, coauthors):
    parts = []
    for first, last in split_names(field):
        name = latex_to_text(f"{first} {last}".strip())
        if name in SELF_NAMES:
            parts.append(f"<strong>{esc(name)}</strong>")
        elif name in coauthors:
            parts.append(f'<a href="{html.escape(coauthors[name])}">{esc(name)}</a>')
        else:
            parts.append(esc(name))
    if len(parts) <= 2:
        return " and ".join(parts)
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def paper_html(entry, coauthors):
    """One publication in the filmography: year, title, authors, venue, buttons."""
    fields = {name: value for name, (value, _) in entry["fields"].items()}
    key = entry["key"]

    venue = esc(latex_to_text(fields.get("label", "")))
    if fields.get("abbr", "").lower() not in ("", "article"):
        venue += f' <span class="tag">{esc(fields["abbr"])}</span>'

    buttons, panels = [], []
    if "abstract" in fields:
        buttons.append(f'<button class="btn" type="button" aria-expanded="false" aria-controls="{key}-abstract">Abstract</button>')
        panels.append(f'<div class="panel" id="{key}-abstract" hidden><p>{esc(latex_to_text(fields["abstract"]))}</p></div>')
    if fields.get("bibtex_show", "").strip().lower() == "true":
        buttons.append(f'<button class="btn" type="button" aria-expanded="false" aria-controls="{key}-bibtex">BibTeX</button>')
        panels.append(
            f'<div class="panel" id="{key}-bibtex" hidden><pre id="{key}-bibtex-text">{esc(bibtex_text(entry))}</pre>'
            f'<button class="btn copy" type="button" data-copy="{key}-bibtex-text">Copy BibTeX</button></div>'
        )
    if "arxiv" in fields:
        buttons.append(f'<a class="btn" href="https://arxiv.org/abs/{html.escape(fields["arxiv"])}">arXiv</a>')
    for field, label, is_pdf in PAPER_BUTTONS:
        if field in fields:
            url = fields[field]
            if is_pdf and "://" not in url:
                url = "/assets/pdf/" + urllib.parse.quote(url)
            target = ' target="_blank"' if url.startswith("/") else ""
            buttons.append(f'<a class="btn" href="{html.escape(url)}"{target}>{label}</a>')

    return f"""<li class="film" id="{key}">
  <span class="year">{esc(fields.get("year", ""))}</span>
  <div class="film-body">
    <h3>{esc(latex_to_text(fields.get("title", "")))}</h3>
    <div class="authors">{authors_html(fields.get("author", ""), coauthors)}</div>
    <div class="venue">{venue}</div>
    <div class="actions">{"".join(buttons)}</div>
    {"".join(panels)}
  </div>
</li>"""


def filmography_html(entries, coauthors):
    items = "\n".join(paper_html(entry, coauthors) for entry in entries)
    return f'<ol class="films">\n{items}\n</ol>'


# --- Page pieces --------------------------------------------------------------


def marquee_html():
    """The marquee's changeable letters, each slightly out of line; the R in
    the surname hangs loose. Seeded, so every build looks the same."""

    def line(text, cls, loose=None):
        rand = random.Random(text)
        words, letters = [], []
        for i, ch in enumerate(text + " "):
            if ch == " ":
                # Letters are grouped into words so narrow screens wrap between words.
                words.append(f'<span class="word">{"".join(letters)}</span>')
                letters = []
                continue
            style = f"transform: translateY({rand.uniform(-.03, .03):.3f}em) rotate({rand.uniform(-1.5, 1.5):.2f}deg)"
            cls_l = "l loose" if i == loose else "l"
            letters.append(f'<span class="{cls_l}" style="{style}">{esc(ch)}</span>')
        return f'<span class="line {cls}" aria-hidden="true">{"".join(words)}</span>'

    name = NAME.upper()
    return line(name, "big", loose=name.find("R", len(FIRST_NAME))) + "\n" + line(MARQUEE_SUBTITLE.upper(), "small")


def projects_html():
    data = load_toml("projects.toml")
    projects = data["project"]
    out = []
    for category in dict.fromkeys(p["category"] for p in projects):
        posters = []
        for p in projects:
            if p["category"] != category:
                continue
            title = p.get("poster_title", p["title"])
            long = " long" if len(title) > 12 else ""
            links = [f'<a class="btn" href="{html.escape(p["url"])}">Website</a>']
            if "github" in p:
                links.append(f'<a class="btn" href="{html.escape(p["github"])}">Code</a>')
            posters.append(f"""<article>
  <div class="lightbox">
    <div class="poster" style="--poster-bg: {p['color']}; --poster-glow: {p['glow']}" aria-hidden="true">
      <span class="presents">{esc(p['presents'])}</span>
      <div class="marquee-title">
        <span class="title{long}">{esc(title)}</span>
        <span class="rule"></span>
        <span class="slogan">{esc(p['slogan'])}</span>
      </div>
      <span class="billing">{esc(p['billing'])}</span>
    </div>
  </div>
  <div class="caption">
    <h3><a href="{html.escape(p['url'])}">{esc(p['title'])}</a></h3>
    <p>{esc(p['description'])}</p>
    <div class="actions">{"".join(links)}</div>
  </div>
</article>""")
        label = f"{data['categories'].get(category, category)} · {category.capitalize()}"
        out.append(f'<div class="showing">\n<p class="eyebrow">{esc(label)}</p>\n<div class="posters">\n{"".join(posters)}\n</div>\n</div>')
    return "\n".join(out)


def teaching_html():
    data = load_toml("teaching.toml")
    tickets = []
    serial = 237
    for course in data["course"]:
        if course.get("current"):
            corner = '<span class="stamp">Now showing</span>'
        else:
            corner = f"<span>Nº {serial:06d}</span>"
            serial += 1009
        tickets.append(f"""<div class="ticket">
  <div class="stub" aria-hidden="true">Admit one</div>
  <div class="ticket-body">
    <div class="course"><a href="{html.escape(course['url'])}">{esc(course['name'])}</a></div>
    <div class="meta"><span>{esc(course['term'])}</span>{corner}</div>
  </div>
</div>""")
    return (
        f'<p class="venue-line">{esc(data["role"])} at <a href="{html.escape(data["institution_url"])}">{esc(data["institution"])}</a></p>\n'
        f'<div class="tickets">\n{"".join(tickets)}\n</div>'
    )


def post_meta(post):
    meta = post["topic"]
    if "date" in post:
        meta += f" · {post['date']:%B} {post['date'].day}, {post['date'].year}"
    return esc(meta)


def posts_html(posts):
    items = []
    for post in posts:
        url = f"/hobbies/{post['slug']}/"
        items.append(f"""<li class="post-item">
  <span class="post-tag">{post_meta(post)}</span>
  <h3><a href="{url}">{esc(post['title'])}</a></h3>
  <p>{esc(post['excerpt'])}</p>
  <a class="read-more" href="{url}">Read →</a>
</li>""")
    return f'<ol class="posts">\n{"".join(items)}\n</ol>'


def social_html():
    # Percent-encode the address so naive scrapers don't pick it up.
    email = "".join(c if c in ".@" else f"%{ord(c):02X}" for c in EMAIL)
    return "\n".join([
        f'<a href="mailto:{email}">Email</a>',
        f'<a href="https://github.com/{GITHUB_USERNAME}">GitHub</a>',
        f'<a href="https://www.linkedin.com/in/{LINKEDIN_USERNAME}">LinkedIn</a>',
    ])


def nav_html(active):
    items = [("about", "/"), ("cv ↗", CV)] + NAV
    out = []
    for title, url in items:
        attrs = ' target="_blank"' if url == CV else ""
        if title == active:
            attrs += ' aria-current="page"'
        out.append(f'<a href="{url}"{attrs}>{title}</a>')
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


def write_page(path, url, *, title, content, active=None, description="", body_class=""):
    today = datetime.date.today()
    page = render(
        "base.html",
        title=f"{NAME} | {title}" if title else NAME,
        name=NAME,
        description=html.escape(description),
        canonical=SITE_URL + url,
        marquee=marquee_html(),
        tagline=esc(TAGLINE),
        nav=nav_html(active),
        content=content,
        updated=f"{today:%B} {today.day}, {today.year}",
        body_class=body_class,
    )
    out = OUT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(open_external_links_in_new_tab(page))


def write_section(name, eyebrow, content):
    """A top-level page such as /projects/, with its heading."""
    content = render("page.html", eyebrow=esc(eyebrow), heading=esc(name.capitalize()), content=content)
    write_page(f"{name}/index.html", f"/{name}/", title=name, content=content, active=name)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "public", OUT)
    # Serve the files as they are; don't let GitHub Pages run Jekyll on them.
    (OUT / ".nojekyll").touch()

    papers = parse_bibtex((ROOT / "data" / "papers.bib").read_text())
    coauthors = load_toml("coauthors.toml")
    selected = [p for p in papers if p["fields"].get("selected", ("",))[0].strip().lower() == "true"]
    posts = load_toml("posts.toml")["post"]

    about = render(
        "about.html",
        name=NAME,
        content=(ROOT / "pages" / "about.html").read_text(),
        social=social_html(),
        selected_papers=filmography_html(selected, coauthors),
    )
    write_page("index.html", "/", title="", content=about, active="about")

    write_section("projects", "In the lobby", projects_html())
    write_section("publications", "Filmography", filmography_html(papers, coauthors))
    write_section("teaching", "Ticket stubs", teaching_html())

    hobbies = f'<div class="prose">\n{(ROOT / "pages" / "hobbies.html").read_text()}</div>\n{posts_html(posts)}'
    write_section("hobbies", "Staff picks", hobbies)
    for post in posts:
        content = render(
            "post.html",
            meta=post_meta(post),
            title=esc(post["title"]),
            content=(ROOT / "pages" / "posts" / f"{post['slug']}.html").read_text(),
        )
        url = f"/hobbies/{post['slug']}/"
        write_page(f"hobbies/{post['slug']}/index.html", url, title=post["title"], content=content, active="hobbies", description=post["excerpt"])

    write_page(
        "404.html",
        "/404.html",
        title="Page not found",
        content=(ROOT / "pages" / "404.html").read_text(),
        description="There is nothing more on this reel.",
        body_class="no-signal",
    )

    urls = ["/"] + [url for _, url in NAV] + [f"/hobbies/{post['slug']}/" for post in posts]
    locs = "\n".join(f"<url><loc>{SITE_URL}{url}</loc></url>" for url in urls)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{locs}\n</urlset>\n'
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
