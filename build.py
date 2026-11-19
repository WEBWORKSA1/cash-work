#!/usr/bin/env python3
"""Static site builder for Cash.Work.

Renders page fragments in src/ into finished HTML files at the repo root,
prerenders live data (jobs, news, videos, gig directory) into the pages so
crawlers see real content, and writes sitemap.xml.

Standard library only, so it runs unchanged inside GitHub Actions.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DATA = ROOT / "data"
SITE = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
TODAY = dt.date.today().isoformat()
LAUNCH = "2026-11-19"

META_RE = re.compile(r"^\s*<!--meta\s+(\{.*?\})\s*-->\s*", re.S)
TOKEN_RE = re.compile(r"\{\{\s*([a-z_:]+)\s*\}\}")


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def load_json(name: str, default):
    path = DATA / name
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return d.strftime("%b %-d, %Y")
    except ValueError:
        return iso[:10]


# ---------------------------------------------------------------- fragments
def read_fragment(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = META_RE.match(text)
    if not m:
        raise SystemExit(f"Missing <!--meta {{...}} --> header in {path}")
    meta = json.loads(m.group(1))
    return meta, text[m.end():]


def collect_pages() -> list[dict]:
    pages = []
    for folder, prefix in (("pages", ""), ("tools", "tools/"), ("guides", "guides/")):
        for path in sorted((SRC / folder).glob("*.html")):
            meta, body = read_fragment(path)
            meta["out"] = prefix + path.name
            meta["depth"] = prefix.count("/")
            meta["body"] = body
            meta["section"] = folder
            pages.append(meta)
    return pages


# ---------------------------------------------------------------- data blocks
def ad_unit(kind: str) -> str:
    slot = SITE.get("ad_slots", {}).get(kind, "")
    if not slot:
        return ""  # Auto ads handle placement until manual slot IDs are configured.
    fmt = 'data-ad-format="fluid" data-ad-layout="in-article"' if kind == "in_article" else 'data-ad-format="auto" data-full-width-responsive="true"'
    return (
        '<aside class="ad-wrap" aria-label="Advertisement"><p class="ad-label">Advertisement</p>'
        f'<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(SITE["adsense_client"])}" '
        f'data-ad-slot="{esc(slot)}" {fmt}></ins>'
        "<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></aside>"
    )


SPEED_LABEL = {
    "instant": "Instant cash-out",
    "fast": "1–3 days",
    "weekly": "Weekly",
    "milestone": "After approval",
}


def gigs_rows(gigs: list[dict]) -> str:
    rows = []
    for g in gigs:
        needs = ", ".join(g.get("needs", [])) or "Phone"
        regions = ", ".join(g.get("regions", []))
        rows.append(
            f'<li class="ledger-row" data-id="{esc(g["id"])}" data-cat="{esc(g["category"])}" '
            f'data-speed="{esc(g["speed"])}" data-mode="{esc(g["mode"])}" '
            f'data-regions="{esc(" ".join(g.get("regions", [])))}" data-car="{1 if g.get("car") else 0}" '
            f'data-low="{g.get("pay_low", 0)}">'
            f'<div class="lr-name"><a href="{esc(g["url"])}" rel="nofollow noopener" target="_blank">{esc(g["name"])}</a>'
            f'<span class="lr-cat">{esc(g["category_label"])}</span></div>'
            f'<div class="lr-pay"><strong>{esc(g["pay"])}</strong><span>{esc(g["pay_note"])}</span></div>'
            f'<div class="lr-speed"><span class="speed speed-{esc(g["speed"])}">{esc(SPEED_LABEL.get(g["speed"], g["speed"]))}</span></div>'
            f'<div class="lr-needs">{esc(needs)}<span>{esc(regions)}</span></div>'
            f'<p class="lr-note">{esc(g["summary"])}</p>'
            "</li>"
        )
    return "\n".join(rows)


def jobs_rows(jobs: list[dict], limit: int) -> str:
    if not jobs:
        return (
            '<li class="empty-state">The live feed is refreshing. New remote jobs from Remotive, Jobicy, '
            'Himalayas, Arbeitnow and Remote OK load here every six hours.</li>'
        )
    out = []
    for j in jobs[:limit]:
        rel = "noopener" if j.get("source") == "Remote OK" else "nofollow noopener"
        salary = f'<span class="job-salary">{esc(j["salary"])}</span>' if j.get("salary") else ""
        out.append(
            '<li class="job-row">'
            f'<a class="job-title" href="{esc(j["url"])}" rel="{rel}" target="_blank">{esc(j["title"])}</a>'
            f'<span class="job-company">{esc(j.get("company"))}</span>'
            f'<span class="job-meta">{esc(j.get("location") or "Remote")}{(" / " + esc(j["type"])) if j.get("type") else ""}</span>'
            f"{salary}"
            f'<span class="job-src">via {esc(j.get("source"))}, {esc(fmt_date(j.get("date", "")))}</span>'
            "</li>"
        )
    return "\n".join(out)


def diverse(jobs: list[dict], n: int) -> list[dict]:
    """Newest jobs, taken round-robin across sources so one board doesn't fill the preview."""
    by_src: dict[str, list] = {}
    for j in jobs:
        by_src.setdefault(j.get("source", ""), []).append(j)
    out, i = [], 0
    while len(out) < n and any(len(v) > i for v in by_src.values()):
        for v in by_src.values():
            if len(v) > i and len(out) < n:
                out.append(v[i])
        i += 1
    return out


def news_rows(news: list[dict], limit: int) -> str:
    if not news:
        return '<li class="empty-state">Headlines refresh every six hours.</li>'
    return "\n".join(
        f'<li class="news-row"><a href="{esc(n["url"])}" rel="nofollow noopener" target="_blank">{esc(n["title"])}</a>'
        f'<span>{esc(n.get("source"))}, {esc(fmt_date(n.get("date", "")))}</span></li>'
        for n in news[:limit]
    )


def video_cards(videos: list[dict], limit: int) -> str:
    if not videos:
        return ""
    out = []
    for v in videos[:limit]:
        vid = esc(v["id"])
        out.append(
            f'<li class="video"><button class="video-play" type="button" data-video="{vid}" '
            f'aria-label="Play video: {esc(v["title"])}">'
            f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"></button>'
            f'<p class="video-title">{esc(v["title"])}</p><p class="video-channel">{esc(v.get("channel"))}</p></li>'
        )
    return "\n".join(out)


def guides_list(pages: list[dict], limit: int | None = None) -> str:
    guides = [p for p in pages if p["section"] == "guides" and p["out"] != "guides/index.html"]
    guides.sort(key=lambda p: p.get("date", ""), reverse=True)
    if limit:
        guides = guides[:limit]
    return "\n".join(
        f'<li class="guide-row"><a href="{{{{root}}}}{esc(p["out"])}">{esc(p["title"])}</a>'
        f'<p>{esc(p["description"])}</p><span>{esc(p.get("read", ""))}</span></li>'
        for p in guides
    )


# ---------------------------------------------------------------- layout
def nav_html(root: str, active: str) -> str:
    items = []
    for label, href in SITE["nav"]:
        cur = ' aria-current="page"' if href == active or (active.startswith(href.split("/")[0] + "/") and "/" in href) else ""
        items.append(f'<li><a href="{root}{href}"{cur}>{esc(label)}</a></li>')
    return "\n".join(items)


def footer_html(root: str) -> str:
    cols = []
    for title, links in SITE["footer"].items():
        lis = "".join(f'<li><a href="{root}{href}">{esc(label)}</a></li>' for label, href in links)
        cols.append(f'<div class="foot-col"><h2>{esc(title)}</h2><ul>{lis}</ul></div>')
    return "\n".join(cols)


def jsonld_base(page: dict, url: str) -> list[dict]:
    blocks = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": SITE["name"],
            "url": SITE["base_url"],
            "potentialAction": {
                "@type": "SearchAction",
                "target": SITE["base_url"] + "gigs.html?q={search_term_string}",
                "query-input": "required name=search_term_string",
            },
        }
    ]
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE["base_url"]}]
    if page["out"] != "index.html":
        if page["section"] in ("guides", "tools") and not page["out"].endswith("index.html"):
            sec = "Guides" if page["section"] == "guides" else "Tools"
            crumbs.append({"@type": "ListItem", "position": 2, "name": sec, "item": SITE["base_url"] + page["section"] + "/index.html"})
        crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": page["title"], "item": url})
        blocks.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs})
    if page["section"] == "guides" and page["out"] != "guides/index.html":
        blocks.append(
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": page["title"],
                "description": page["description"],
                "datePublished": page.get("date", LAUNCH),
                "dateModified": page.get("modified", page.get("date", LAUNCH)),
                "author": {"@type": "Organization", "name": "Cash.Work editorial team"},
                "publisher": {"@type": "Organization", "name": SITE["name"]},
                "mainEntityOfPage": url,
            }
        )
    if page.get("faq"):
        blocks.append(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in page["faq"]
                ],
            }
        )
    return blocks


def render(page: dict, ctx: dict) -> str:
    root = "/" if page.get("absolute") else "../" * page["depth"]
    url = SITE["base_url"] + ("" if page["out"] == "index.html" else page["out"])
    title = page["title"] if page["out"] == "index.html" else f'{page["title"]} | {SITE["name"]}'

    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key == "root":
            return root
        if key.startswith("ad:"):
            return ad_unit(key[3:])
        val = ctx.get(key)
        if val is None:
            raise SystemExit(f"Unknown token {{{{{key}}}}} in {page['out']}")
        return val

    page = dict(page)
    page["title"] = TOKEN_RE.sub(sub, page["title"])
    page["description"] = TOKEN_RE.sub(sub, page["description"])
    title = page["title"] if page["out"] == "index.html" else f'{page["title"]} | {SITE["name"]}'
    body = TOKEN_RE.sub(sub, page["body"])
    body = TOKEN_RE.sub(sub, body)  # second pass for tokens produced by blocks (guides list)

    scripts = "".join(f'<script src="{root}assets/js/{s}" defer></script>' for s in page.get("scripts", []))
    robots = '<meta name="robots" content="noindex, follow">' if page.get("noindex") else '<meta name="robots" content="index, follow, max-image-preview:large">'
    ld = "\n".join(
        f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>' for b in jsonld_base(page, url)
    )
    og_type = "article" if page["section"] == "guides" and page["out"] != "guides/index.html" else "website"
    strip = SITE["contact_strip"]

    return f"""<!doctype html>
<html lang="{SITE['locale']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(page['description'])}">
{robots}
<link rel="canonical" href="{esc(url)}">
<meta name="theme-color" content="{SITE['theme_color']}">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(page['title'])}">
<meta property="og:description" content="{esc(page['description'])}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{SITE['base_url']}assets/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}assets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{root}assets/img/icon-192.png">
<link rel="manifest" href="{root}manifest.webmanifest">
<link rel="preload" href="{root}assets/fonts/archivo-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}assets/fonts/public-sans-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/css/site.css?v={ctx['build_id']}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={SITE['adsense_client']}" crossorigin="anonymous"></script>
{ld}
</head>
<body class="page-{esc(page['out'].replace('/', '-').replace('.html', ''))}">
<a class="skip" href="#main">Skip to content</a>
<div class="contact-strip"><a href="{esc(strip['href'])}" rel="noopener" target="_blank">{esc(strip['text'])}</a></div>
<header class="site-head">
  <div class="wrap head-inner">
    <a class="brand" href="{root}index.html" aria-label="Cash.Work home"><span class="brand-mark" aria-hidden="true"></span><span>Cash<span class="brand-dot">.</span>Work</span></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
    <nav id="site-nav" class="site-nav" aria-label="Main">
      <ul>{nav_html(root, page['out'])}</ul>
      <a class="btn btn-small" href="{root}get-matched.html">Get matched</a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div class="foot-top">
      <div class="foot-brand">
        <a class="brand" href="{root}index.html"><span class="brand-mark" aria-hidden="true"></span><span>Cash<span class="brand-dot">.</span>Work</span></a>
        <p>Legit ways to earn, ranked by how fast they pay. Independent, reader-supported and updated every six hours.</p>
        <p class="foot-updated">Data last refreshed {esc(ctx['updated_human'])}.</p>
      </div>
      {footer_html(root)}
    </div>
    <div class="foot-legal">
      <p>Cash.Work is an independent publication. It is not affiliated with, endorsed by or sponsored by any business that uses a similar name, or by any platform listed on this site. Platform names and logos belong to their owners and are used only to identify them. Pay figures are estimates gathered from public sources and vary by city, season and effort; they are not promises of income. Read the <a href="{root}disclaimer.html">full disclaimers</a>.</p>
      <p>&copy; {dt.date.today().year} Cash.Work. Original text, tools and design are protected by copyright. All rights reserved.</p>
    </div>
  </div>
</footer>
<div class="cookie" id="cookie" hidden>
  <p>We use cookies for basic site features and, through Google AdSense, to show ads. See the <a href="{root}privacy.html">privacy policy</a> for your choices.</p>
  <button class="btn btn-small" type="button" data-cookie-ok>OK</button>
</div>
<script src="{root}assets/js/app.js?v={ctx['build_id']}" defer></script>
{scripts}
</body>
</html>
"""


# ---------------------------------------------------------------- sitemap
def sitemap(pages: list[dict]) -> str:
    dynamic = {"index.html", "jobs.html", "news.html", "videos.html", "gigs.html"}
    urls = []
    for p in pages:
        if p.get("noindex"):
            continue
        loc = SITE["base_url"] + ("" if p["out"] == "index.html" else p["out"])
        lastmod = TODAY if p["out"] in dynamic else p.get("modified", p.get("date", LAUNCH))
        prio = "1.0" if p["out"] == "index.html" else ("0.9" if p["out"] in dynamic else "0.7")
        urls.append(f"  <url><loc>{esc(loc)}</loc><lastmod>{lastmod}</lastmod><priority>{prio}</priority></url>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"


def main() -> None:
    gigs = load_json("gigs.json", {"gigs": []})["gigs"]
    jobs = load_json("jobs.json", {"jobs": []}).get("jobs", [])
    news = load_json("news.json", {"items": []}).get("items", [])
    videos = load_json("videos.json", {"videos": []}).get("videos", [])
    meta = load_json("meta.json", {})
    updated = meta.get("updated", "")
    pages = collect_pages()

    ctx = {
        "build_id": dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M"),
        "updated_human": fmt_date(updated) if updated else "at launch",
        "jobs_count": f"{len(jobs):,}" if jobs else "hundreds of",
        "gigs_count": str(len(gigs)),
        "gig_rows": gigs_rows(gigs),
        "gig_rows_fast": gigs_rows([g for g in gigs if g["speed"] == "instant"][:8]),
        "job_rows": jobs_rows(jobs, 60),
        "job_rows_short": jobs_rows(diverse(jobs, 8), 8),
        "news_rows": news_rows(news, 40),
        "news_rows_short": news_rows(news, 6),
        "video_cards": video_cards(videos, 24),
        "video_cards_short": video_cards(videos, 4),
        "guides_list": guides_list(pages),
        "guides_list_short": guides_list(pages, 4),
        "year": str(dt.date.today().year),
    }

    for page in pages:
        out = ROOT / page["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(page, ctx), encoding="utf-8")

    (ROOT / "sitemap.xml").write_text(sitemap(pages), encoding="utf-8")
    print(f"Built {len(pages)} pages; {len(gigs)} gigs, {len(jobs)} jobs, {len(news)} headlines, {len(videos)} videos.")


if __name__ == "__main__":
    main()
