# youhide.com.br

Personal site. Plain static HTML — no framework, no build step, no dependencies.

Deployed to GitHub Pages by [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)
on every push to `main`.

## Layout

```
site/          everything that gets published
  index.html
  about/
  projects/
  blog/
    index.html            post list + tag filter
    <slug>/index.html     one folder per post
  feed.xml     RSS, maintained by hand
  404.html
  css/style.css
  js/main.js   language toggle and blog tag filter, the only script
assets/        source files, NOT published
```

## Preview

```bash
python3 -m http.server 8000 --directory site
```

Then open <http://localhost:8000>. The URL structure is identical to production.

## Adding a post

There is no build step, so a new post touches five files. In order:

1. `site/blog/<slug>/index.html` — copy the closest existing post and replace the
   `<title>`, the meta/OG block, the canonical URL, the `<h1>` pair, the date and
   the tags. Asset paths are `../../`.
2. `site/blog/index.html` — add an `<li data-tags="...">` at the top of `.posts`.
   The tags in `data-tags` are what the filter buttons match; add a new button to
   `.filters` if the tag is new.
3. `site/index.html` — add the same item to the `$ tail -n 3 ~/blog` section and
   drop the oldest, keeping three.
4. `site/feed.xml` — add an `<item>` at the top of the channel.
5. `site/sitemap.xml` — add the post URL.

Posts are bilingual like the rest of the site: every block element is written
twice, tagged `lang="en"` and `lang="pt-BR"`. The RSS feed carries the English
summary only.

## Notes

- **Zero external requests.** System monospace stack, inline SVG icons, no CDN.
- **Bilingual (EN / PT-BR).** Both languages live in the HTML; CSS hides the
  inactive one and `js/main.js` flips `data-lang` on `<html>`. Works without JS,
  defaulting to English.
- **The tag filter is progressive enhancement.** The buttons are `hidden` in the
  markup and unhidden by the script, so with JS off every post stays visible
  instead of leaving dead controls on the page.
- **Paths are relative** everywhere except `404.html`, which uses root-absolute
  paths because Pages serves it at the requested URL.
- **No `CNAME` file.** With the Actions/artifact deploy, GitHub ignores it — the
  custom domain lives in Settings → Pages.
- **Theme** derives from the header SVG on [github.com/youhide](https://github.com/youhide)
  (Dracula palette, terminal chrome).
