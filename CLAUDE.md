# CLAUDE.md — working conventions for youhide.com.br

Guidance for Claude Code and any developer working in this repository.

## What this project is

A personal site: hand-written static HTML, no framework, no build step, no
dependencies. `site/` is the published tree — GitHub Pages uploads it verbatim as an
artifact ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)) on every push
to `main`. `assets/` holds sources and tooling and is never published.

There was a static site generator here until August 2026. It was removed because two
pages of content did not justify a theme submodule pinned to a 2019 commit and an FTP
deploy action pinned to a mutable `@master` ref. Anything that reintroduces a build
step, a dependency, or an external request is a regression, not an improvement.

```bash
python3 -m http.server 8000 --directory site   # preview; URLs identical to production
python3 assets/check-site.py                   # run before every commit — CI runs it too
./assets/render-assets.sh                      # regenerate favicons/og/avatar (macOS only)
```

`render-assets.sh` uses `sips` and `qlmanage`, both macOS built-ins. It is run by hand
and only when `assets/og.svg`, `assets/avatar-source.png` or `site/favicon.svg` change.

## The inviolable rules

Break these and the change is wrong regardless of how convenient it is.

### 1. Zero external requests

System monospace stack, inline SVG icons, no CDN, no web font service, no analytics.
Outbound `<a href>` links to other sites are expected and fine — this is about
subresources. A `<script>`, `<img>`, `<link rel=stylesheet>` or `@font-face` pointing at
another host is a defect: it hands a third party the ability to change or observe the
page. `check-site.py` fails the deploy on one.

### 2. Bilingual EN / PT-BR, in parity

Every translatable element exists twice, tagged `lang="en"` and `lang="pt-BR"`. CSS
hides the inactive one ([`site/css/style.css:87`](site/css/style.css#L87)) and
[`site/js/main.js`](site/js/main.js) flips `data-lang` on `<html>`. The script is loaded
synchronously in `<head>` so the language is set before the body paints; with JS
disabled the page keeps the language hardcoded in the file and still renders.

A missing translation throws no error and logs nothing — the paragraph simply vanishes
when the toggle flips. That silence is the entire reason `check-site.py` counts the
pairs on every page.

### 3. Relative paths, except in `404.html`

Every page uses relative paths; depth matters (`../../` in a post, `../` in the blog
index). [`site/404.html`](site/404.html) is the one exception and uses root-absolute
paths, because Pages serves that file **at the requested URL** — relative paths would
resolve against the missing directory and 404 alongside it, leaving an unstyled error
page. Do not "fix" it to match the others.

### 4. `site/` is published literally

There is no filter between the folder and the domain. A `.DS_Store`, an editor backup or
a stray draft committed under `site/` is served to the public. `check-site.py` fails on
one that git tracks and warns on one that is merely present locally.

### 5. The footer is duplicated in every page, and it has drifted before

The same 24-line footer block is copied into all seven pages. `404.html` carried a
reduced copy for months and nobody noticed. Editing the footer is a seven-file edit;
`check-site.py` compares the copies and fails when one diverges. The same applies to the
nav block, which differs between pages only by path depth and by which link carries
`aria-current="page"`.

## Adding a post

Use the [`new-blog-post`](.claude/skills/new-blog-post/SKILL.md) skill. It exists because
a post is a five-file edit and four of those files are easy to forget. The procedure
lives there and nowhere else, so the two copies cannot disagree.

## Content conventions

- **Verify before asserting.** Release years, version numbers, test counts and dates get
  checked against a source, not recalled. A plausible-sounding date in published prose is
  worse than an omission, and the site owner reads closely.
- **Never publish a placeholder.** No `20??`, no `TODO`, no lorem. If a fact is missing,
  leave the line out and say so — this repo can be pushed at any moment.
- **Never link a private repository.** It renders as a 404 for every visitor. Link the
  post that describes the project instead, and mark the card as private.
- **Prefer specifics over adjectives.** "3506 bytes duplicated across seven pages" is
  useful; "lots of duplication" is not.

## Code style

- Two-space indent in HTML and CSS. Four in Python.
- CSS follows the existing block order and the section comment banners already in
  [`site/css/style.css`](site/css/style.css). Colors come from the `:root` tokens; no
  raw hex outside that block.
- `site/js/main.js` is ES5-flavoured, uses `var`, wraps each feature in its own IIFE, and
  guards on element presence so a page without that feature is unaffected. It is the only
  script on the site and it stays that way.
- Progressive enhancement is not optional: the blog tag filter ships its buttons
  `hidden` and the script unhides them, so with JS off there are no dead controls.
- Comment the *why*. The `qlmanage` square-thumbnail workaround in `render-assets.sh` and
  the root-absolute note in `404.html` are the model.

## Commits

- Conventional Commits, imperative, in English: `blog:`, `site:`, `css:`, `ci:`, `docs:`.
- Commit directly to `main` — solo project, no PR flow. The deploy gate is
  `check-site.py`, not a review.
- Never commit without running `python3 assets/check-site.py` first.

## Files to keep in sync

A new post touches five files. Miss one and the post is live but invisible, or listed but
missing:

| File | What goes in |
|---|---|
| `site/blog/<slug>/index.html` | the post itself |
| `site/blog/index.html` | an `<li data-tags="…">` at the top of `.posts` |
| `site/index.html` | the same item in `$ tail -n 3 ~/blog`, keeping three |
| `site/feed.xml` | an `<item>` at the top of the channel |
| `site/sitemap.xml` | a `<url>` for the post |

Other coupled edits: a new tag needs a `.filters` button in `site/blog/index.html`; a
footer or nav change is a seven-file edit; a change to how posts are added must update
the skill **and** the `## Adding a post` section of [`README.md`](README.md).

This file is a living document — update it in the same commit as the change it describes.
