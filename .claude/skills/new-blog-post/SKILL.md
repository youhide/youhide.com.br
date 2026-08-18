---
name: new-blog-post
description: Use when adding a post to the youhide.com.br blog. The site is hand-written static HTML with no build step, so a post is a five-file edit — the post page itself plus the blog index, the home page's latest-posts block, feed.xml and sitemap.xml — and every post is bilingual EN/PT-BR in the same markup. This skill lists the exact strings that change and the exact snippets to insert, so nothing ships live-but-invisible. Trigger on any request to "write a blog post", "add a post", "publish a post", "escrever um post", or "adicionar um post ao blog".
---

# New blog post (youhide.com.br)

No generator, no templates, no frontmatter. A post is a complete HTML document in its
own folder, and four other files have to learn about it. See the root
[`CLAUDE.md`](../../../CLAUDE.md) for the site-wide rules that apply here — zero external
requests, bilingual parity, relative paths.

Canonical reference to copy the shape from: **the most recent post**, currently
`site/blog/greenvale/index.html`. Copy that, not a template. A template file would be an
eighth copy of the footer block, and the seventh (`site/404.html`) silently drifted for
months — which is exactly the failure this repo already has evidence of.

## 0. Confirm with the user first

Ask (use `AskUserQuestion`) for what is not derivable from the request:

- **Slug** — kebab-case, becomes the folder name and the URL (`/blog/<slug>/`).
- **Date** — the `datetime` attribute and the visible text, `YYYY-MM-DD`. Use today's
  date unless told otherwise; never guess a past date.
- **Tags** — lowercase, from the existing set where one fits (`meta`, `homelab`, `rust`,
  `go`, `gamedev`, `design`, `kubernetes`, `html`, `github-actions`). A genuinely new tag
  also needs a button in `.filters` (step 2).
- **Both titles** — EN and PT-BR. They are separate `<h1>` elements, not a translation
  pass done later.

If the post is about a project, also confirm whether its repository is public. A private
repo must never be linked — it is a 404 for every visitor.

## 1. Create `site/blog/<slug>/index.html`

Copy the most recent post verbatim, then change **exactly** this list. Everything outside
`<article>` is otherwise byte-identical across posts, and the footer check enforces it:

| Location | What changes |
|---|---|
| `<title>` | `<EN title> — youHide` |
| `meta[name=description]` | one sentence, English |
| `link[rel=canonical]` | `https://youhide.com.br/blog/<slug>/` |
| `meta[property=article:published_time]` | the date |
| `og:title`, `og:description`, `og:url` | per post; `og:type` stays `article` |
| the prompt line | `$ cat <slug>.md` |
| both `<h1 class="page__title">` | EN keeps `id="page-title"`, PT-BR carries no id |
| `<time class="post-date">` | **the date appears twice** — the `datetime` attribute and the element text |
| `<ul class="post-tags">` | one `<li>` per tag |

Asset paths stay at `../../`. The nav's blog link keeps `aria-current="page"`.

The body goes inside `<article class="section post prose">`. Every block element is
written twice, `lang="en"` then `lang="pt-BR"` — paragraphs, headings, list wrappers,
blockquotes. `<pre>` code blocks are language-neutral and are written once. Available
prose elements are styled already: `h2` (renders with a `##` prefix), `p`, `ul`/`ol`,
`pre`, `code`, `blockquote`, `hr`, `strong`, `em`.

## 2. Add it to `site/blog/index.html`

At the **top** of `.posts`, so the list stays newest-first:

```html
        <li data-tags="tag1 tag2">
          <a class="post-item" href="<slug>/">
            <div class="post-item__top">
              <time class="post-date" datetime="YYYY-MM-DD">YYYY-MM-DD</time>
              <ul class="post-tags">
                <li>tag1</li><li>tag2</li>
              </ul>
            </div>
            <h3 class="post-item__title" lang="en">…</h3>
            <h3 class="post-item__title" lang="pt-BR">…</h3>
            <p class="post-item__excerpt" lang="en">…</p>
            <p class="post-item__excerpt" lang="pt-BR">…</p>
          </a>
        </li>
```

`data-tags` is what the filter matches — it must list every tag, space-separated. A new
tag needs a matching button added to `.filters`:

```html
        <button class="filter" type="button" data-filter="newtag" aria-pressed="false">newtag</button>
```

## 3. Add it to `$ tail -n 3 ~/blog` in `site/index.html`

The same `<li>`, with two differences: `href="blog/<slug>/"` and a shorter excerpt (one
sentence — the home page is not the index). Keep **three** items: adding the new one at
the top means dropping the oldest.

## 4. Add an `<item>` to `site/feed.xml`

At the top of the channel, newest first:

```xml
    <item>
      <title>…</title>
      <link>https://youhide.com.br/blog/<slug>/</link>
      <guid isPermaLink="true">https://youhide.com.br/blog/<slug>/</guid>
      <pubDate>Tue, 18 Aug 2026 09:30:00 -0300</pubDate>
      <category>tag1</category>
      <category>tag2</category>
      <description>…</description>
    </item>
```

`pubDate` is RFC 822 with the `-0300` offset. The feed is English-only — the channel
description says so — so title and description are the EN versions, not both languages.

## 5. Add a `<url>` to `site/sitemap.xml`

Above the older posts:

```xml
  <url>
    <loc>https://youhide.com.br/blog/<slug>/</loc>
    <lastmod>YYYY-MM-DD</lastmod>
    <priority>0.6</priority>
  </url>
```

## Verify

```bash
python3 assets/check-site.py                     # must exit 0 — CI runs this same script
python3 -m http.server 8000 --directory site     # then open /blog/ and the post
```

The checker catches a post missing from the index, feed or sitemap, a broken relative
path, unbalanced tags, and an EN/PT-BR count mismatch. It cannot tell you the translation
is *bad* — read both languages in the browser and click the EN/PT toggle on the post
page. Also click a tag filter to confirm the new post appears under each of its tags.

## Don't

- ❌ **Write one language and leave the other for later.** The untranslated block does not
  error — it vanishes when the toggle flips, and the page reads as though a paragraph were
  deleted.
- ❌ **Create a post template file.** It becomes another copy of the footer and nav to keep
  in sync. Copy the newest post, which is by definition current.
- ❌ **Link a private repository.** 404 for every visitor. Link the post instead.
- ❌ **Ship a placeholder** like `20??` or a `TODO`. The site can be pushed at any moment.
  Leave the fact out and say what is missing.
- ❌ **State a number, version or release year you have not checked.** Verify against a
  source; if you cannot, omit it and say so.
- ❌ **Add a CDN script, a web font or an analytics snippet.** The deploy fails, by design.
- ❌ **Edit the footer or nav in one page only.** Seven files or none.
- ❌ **Forget `data-tags`.** Without it the post is invisible to every filter but `all`.
