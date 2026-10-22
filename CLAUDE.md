# CLAUDE.md

## Project

Personal website built by `build.py` (Python standard library only, no third-party dependencies). See README.md for the layout. Build with `./build.py`; preview with `./build.py --serve`. Pushing to `master` deploys.

## Design

- The site is a spooky homage to cinema: a movie theatre's programme playing on an old CRT at 3am.
- Spooky, not vintage and not neon: cold, modern palette (near-black, cool greys, moonlight accent; red only for ticket stamps). Dark only.
- No illustrated backdrops and nothing silly (no balloons, no Halloween clip-art). Homage through allusions, never film stills, logos or characters.
- Content stays readable first. Every animation must stop under `prefers-reduced-motion`, and nothing flashes more than 3 times a second.

## Scripts

- Scripts with a shebang must always be executable (`chmod +x`).
- Scripts take their options through `argparse`, and `--help` explains how to use them.

## Git

- Never commit without my explicit authorization. Approval for one commit does not carry over to later ones.
- Keep commit messages concise and to the point: a short title, followed by a short description of what the commit contains.
- Never attribute co-authorship to Claude: no `Co-Authored-By` lines or other Claude/AI attribution in commit messages.
