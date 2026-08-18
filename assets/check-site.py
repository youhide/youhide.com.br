#!/usr/bin/env python3
"""Validate site/ before it is published.

There is no build step, so nothing else stands between an edit and production.
This script is that step. It runs in CI before the Pages upload (see
.github/workflows/deploy.yml) and fails the deploy on any error.

Standard library only, on purpose: the site's rule is zero dependencies, and a
checker that needs a package manager would be the first exception.

    python3 assets/check-site.py

Exit 0 = publishable. Exit 1 = at least one error, each named with file and line.
"""

import hashlib
import os
import re
import sys
import xml.dom.minidom
from html.parser import HTMLParser

SITE = 'site'
DOMAIN = 'https://youhide.com.br'

# Elements that never take a closing tag. `path`/`circle`/`ellipse` are in here
# because the inline SVG icons write them self-closed and HTMLParser does not
# track the SVG namespace's self-closing rules for us.
VOID = {
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
    'param', 'source', 'track', 'wbr',
    'path', 'circle', 'ellipse', 'rect', 'line', 'polygon', 'polyline', 'use', 'stop',
}

# Attributes that load a subresource. An <a href> may point anywhere; these may not.
SUBRESOURCE = {
    ('script', 'src'), ('img', 'src'), ('source', 'src'),
    ('iframe', 'src'), ('video', 'src'), ('audio', 'src'), ('embed', 'src'),
}

# <link> is a subresource only for these rel values. rel=canonical and
# rel=alternate carry absolute public URLs by design and fetch nothing.
SUBRESOURCE_REL = {
    'stylesheet', 'icon', 'apple-touch-icon', 'mask-icon', 'manifest',
    'preload', 'prefetch', 'modulepreload',
}

JUNK = re.compile(r'(^|/)(\.DS_Store|Thumbs\.db|.*~|.*\.orig|.*\.rej|.*\.bak)$')

errors = []
warnings = []


def error(where, msg):
    errors.append('%s  %s' % (where, msg))


def warn(where, msg):
    warnings.append('%s  %s' % (where, msg))


def html_files():
    out = []
    for root, _, files in os.walk(SITE):
        for f in files:
            if f.endswith('.html'):
                out.append(os.path.join(root, f))
    return sorted(out)


# --------------------------------------------------------------------------
# 1. tag nesting, subresource origin, and the link inventory, in one pass
# --------------------------------------------------------------------------

class Page(HTMLParser):
    """Collects nesting errors and every referenced path, with line numbers."""

    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack = []          # (tag, line)
        self.refs = []           # (attr_value, line, is_subresource)
        self.lang_open = []      # (lang_value, line) for parity reporting
        self.doc_lang = None     # the <html lang> — the one legitimate unpaired one

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        d = dict(attrs)

        for attr in ('href', 'src'):
            if not d.get(attr):
                continue
            if tag == 'link':
                rels = d.get('rel', '').lower().split()
                is_sub = any(r in SUBRESOURCE_REL for r in rels)
            else:
                is_sub = (tag, attr) in SUBRESOURCE
            self.refs.append((d[attr], line, is_sub))

        if d.get('lang'):
            if tag == 'html':
                self.doc_lang = d['lang']
            else:
                self.lang_open.append((d['lang'], line))

        if tag not in VOID:
            self.stack.append((tag, line))

    def handle_startendtag(self, tag, attrs):
        # <foo /> — never opens a scope
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        line = self.getpos()[0]
        if tag in VOID:
            return
        if not self.stack:
            error('%s:%d' % (self.path, line), 'stray </%s> with nothing open' % tag)
            return
        if self.stack[-1][0] != tag:
            open_tag, open_line = self.stack[-1]
            error('%s:%d' % (self.path, line),
                  '</%s> closes while <%s> from line %d is still open'
                  % (tag, open_tag, open_line))
            return
        self.stack.pop()


def resolve(page, ref):
    """Map a reference to a path on disk, or None if it is not ours to check."""
    if ref.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', 'data:', '#')):
        return None
    ref = ref.split('#', 1)[0].split('?', 1)[0]
    if not ref:
        return None

    if ref.startswith('/'):
        # Root-absolute. Legal only in 404.html, which Pages serves AT the
        # requested URL, where relative paths would resolve against that URL.
        target = os.path.join(SITE, ref.lstrip('/'))
    else:
        target = os.path.normpath(os.path.join(os.path.dirname(page), ref))

    if ref.endswith('/') or os.path.isdir(target):
        target = os.path.join(target, 'index.html')
    return target


def parse_all():
    parsed = {}
    for page in html_files():
        p = Page(page)
        p.feed(open(page, encoding='utf-8').read())
        p.close()
        parsed[page] = p
    return parsed


def check_pages(parsed):
    for page, p in parsed.items():
        for tag, line in p.stack:
            error('%s:%d' % (page, line), '<%s> is never closed' % tag)

        is_404 = os.path.basename(page) == '404.html'
        for ref, line, is_sub in p.refs:
            where = '%s:%d' % (page, line)

            if is_sub and ref.startswith(('http://', 'https://', '//')):
                error(where, 'external subresource %s — the site makes no outbound '
                             'requests' % ref)
                continue

            if ref.startswith('/') and not is_404:
                error(where, 'root-absolute path %s outside 404.html — every other '
                             'page uses relative paths' % ref)
                continue

            target = resolve(page, ref)
            if target is not None and not os.path.exists(target):
                error(where, 'broken link %s (looked for %s)' % (ref, target))


# --------------------------------------------------------------------------
# 2. bilingual parity
# --------------------------------------------------------------------------

def check_parity(parsed):
    """Every translatable element exists twice: lang="en" and lang="pt-BR".

    Counted from parsed lang attributes, not from grepping the source, so
    `data-lang="en"` on <html> and `title="youHide — blog"` on the RSS <link>
    cannot skew the total. The <html lang> is recorded separately, so it is
    excluded by tag rather than by subtracting one and hoping.
    """
    for page, p in parsed.items():
        en = [(l, n) for l, n in p.lang_open if l == 'en']
        pt = [(l, n) for l, n in p.lang_open if l == 'pt-BR']
        other = [(l, n) for l, n in p.lang_open if l not in ('en', 'pt-BR')]

        for lang, line in other:
            error('%s:%d' % (page, line), 'unexpected lang="%s"' % lang)

        en_count = len(en)
        if en_count != len(pt):
            missing = 'pt-BR' if en_count > len(pt) else 'en'
            error(page, 'bilingual parity: %d en vs %d pt-BR — a %s translation is '
                        'missing, and it will silently vanish when the toggle flips'
                        % (en_count, len(pt), missing))


# --------------------------------------------------------------------------
# 3. XML well-formedness
# --------------------------------------------------------------------------

def check_xml():
    for name in ('feed.xml', 'sitemap.xml'):
        path = os.path.join(SITE, name)
        if not os.path.exists(path):
            error(path, 'missing')
            continue
        try:
            xml.dom.minidom.parse(path)
        except Exception as exc:
            error(path, 'malformed XML: %s' % exc)


# --------------------------------------------------------------------------
# 4. post sync — the check that exists because this is a five-file edit
# --------------------------------------------------------------------------

def posts_on_disk():
    blog = os.path.join(SITE, 'blog')
    if not os.path.isdir(blog):
        return []
    return sorted(
        d for d in os.listdir(blog)
        if os.path.isfile(os.path.join(blog, d, 'index.html'))
    )


def check_post_sync():
    slugs = posts_on_disk()
    if not slugs:
        return slugs

    index = os.path.join(SITE, 'blog', 'index.html')
    home = os.path.join(SITE, 'index.html')
    feed = os.path.join(SITE, 'feed.xml')
    sitemap = os.path.join(SITE, 'sitemap.xml')

    # Match on the href/loc a slug must appear as, not on the bare slug, so a
    # word that happens to occur in prose cannot satisfy the check.
    expected = {
        index:   lambda s: 'href="%s/"' % s,
        home:    lambda s: 'href="blog/%s/"' % s,
        feed:    lambda s: '%s/blog/%s/' % (DOMAIN, s),
        sitemap: lambda s: '%s/blog/%s/' % (DOMAIN, s),
    }

    bodies = {f: open(f, encoding='utf-8').read() for f in expected}

    for slug in slugs:
        for f, pattern in expected.items():
            needle = pattern(slug)
            if needle not in bodies[f]:
                if f == home:
                    # The home page shows the three most recent, not all of them.
                    continue
                error(f, 'post "%s" exists on disk but is not listed here '
                         '(expected to find %s)' % (slug, needle))

    # And the reverse: nothing may point at a post that does not exist.
    for f, body in bodies.items():
        for found in re.findall(re.escape(DOMAIN) + r'/blog/([a-z0-9-]+)/', body):
            if found not in slugs:
                error(f, 'references post "%s", which does not exist in site/blog/'
                      % found)
        for found in re.findall(r'href="(?:blog/)?([a-z0-9-]+)/"', body):
            if f in (index, home) and found not in slugs and found not in (
                    'about', 'projects', 'blog'):
                error(f, 'links to blog post "%s", which does not exist' % found)

    # The newest post should be the one the home page shows.
    newest_listed = re.search(r'href="blog/([a-z0-9-]+)/"', bodies[home])
    if newest_listed and newest_listed.group(1) not in slugs:
        error(home, 'the featured post "%s" does not exist' % newest_listed.group(1))

    return slugs


# --------------------------------------------------------------------------
# 5. the duplicated footer must not drift
# --------------------------------------------------------------------------

def check_footer(parsed):
    """The footer is copied into every page. 404.html once drifted; this is the
    tripwire that makes the next drift fail instead of ship."""
    seen = {}
    for page in parsed:
        src = open(page, encoding='utf-8').read()
        a = src.find('<footer class="footer">')
        if a == -1:
            error(page, 'no footer block')
            continue
        b = src.find('</footer>', a)
        block = src[a:b + len('</footer>')]
        seen.setdefault(hashlib.md5(block.encode()).hexdigest(), []).append(page)

    if len(seen) > 1:
        groups = sorted(seen.values(), key=len, reverse=True)
        majority, rest = groups[0], groups[1:]
        for group in rest:
            for page in group:
                error(page, 'footer differs from the copy shared by the other %d '
                            'pages — edit the footer in every page or not at all'
                            % len(majority))


# --------------------------------------------------------------------------
# 6. nothing unpublishable inside site/
# --------------------------------------------------------------------------

def tracked_files():
    """What CI will actually publish. A fresh checkout has only tracked files, so
    a local .DS_Store is noise here even though a committed one is a real bug."""
    try:
        import subprocess
        out = subprocess.run(['git', 'ls-files', SITE], capture_output=True,
                             text=True, check=True).stdout
        return set(out.split('\n')) - {''}
    except Exception:
        return None


def check_junk():
    tracked = tracked_files()
    for root, dirs, files in os.walk(SITE):
        for f in files:
            path = os.path.join(root, f)
            if not JUNK.search(path):
                continue
            if tracked is None:
                error(path, 'would be published — site/ is uploaded verbatim')
            elif path in tracked:
                error(path, 'is committed and would be published — site/ is '
                            'uploaded verbatim')
            else:
                warn(path, 'exists locally but is untracked, so CI will not '
                           'publish it. Still worth deleting.')


def main():
    if not os.path.isdir(SITE):
        print('error: run from the repository root (no %s/ here)' % SITE)
        return 1

    parsed = parse_all()
    check_pages(parsed)
    check_parity(parsed)
    check_xml()
    slugs = check_post_sync()
    check_footer(parsed)
    check_junk()

    for line in warnings:
        print('warn   %s' % line)

    if errors:
        print()
        for line in errors:
            print('error  %s' % line)
        print('\n%d error%s. Nothing was published.'
              % (len(errors), '' if len(errors) == 1 else 's'))
        return 1

    print('%d pages parsed, links resolved, subresources local' % len(parsed))
    print('%d pages bilingual EN/PT-BR in parity' % len(parsed))
    print('feed.xml and sitemap.xml well-formed')
    print('%d post%s in sync across blog index, feed and sitemap'
          % (len(slugs), '' if len(slugs) == 1 else 's'))
    print('footer identical across %d pages' % len(parsed))
    print('site/ clean')
    return 0


if __name__ == '__main__':
    sys.exit(main())
