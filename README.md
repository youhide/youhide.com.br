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
  404.html
  css/style.css
  js/main.js   language toggle, the only script
assets/        source files, NOT published
```

## Preview

```bash
python3 -m http.server 8000 --directory site
```

Then open <http://localhost:8000>. The URL structure is identical to production.

## Notes

- **Zero external requests.** System monospace stack, inline SVG icons, no CDN.
- **Bilingual (EN / PT-BR).** Both languages live in the HTML; CSS hides the
  inactive one and `js/main.js` flips `data-lang` on `<html>`. Works without JS,
  defaulting to English.
- **Paths are relative** everywhere except `404.html`, which uses root-absolute
  paths because Pages serves it at the requested URL.
- **No `CNAME` file.** With the Actions/artifact deploy, GitHub ignores it — the
  custom domain lives in Settings → Pages.
- **Theme** derives from the header SVG on [github.com/youhide](https://github.com/youhide)
  (Dracula palette, terminal chrome).
