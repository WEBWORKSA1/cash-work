# Cash.Work

Gigs, shifts and remote jobs ranked by how fast they pay. A static, self-updating site built for the GitHub Pages free plan (main branch).

## What's inside

| Path | Purpose |
|---|---|
| `src/pages`, `src/tools`, `src/guides` | Page bodies (HTML fragments with a `<!--meta {...} -->` header) |
| `src/site.json` | Site name, AdSense client, optional manual ad slot IDs, nav, footer, top contact banner link |
| `build.py` | Wraps fragments in the shared layout, prerenders live data, writes HTML and `sitemap.xml` |
| `data/gigs.json` | The curated directory of platforms (edit this to add or update listings) |
| `data/jobs.json`, `videos.json`, `news.json`, `meta.json` | Written automatically by the refresh job |
| `scripts/fetch_data.py` | Pulls remote jobs, creator videos and work headlines |
| `.github/workflows/refresh.yml` | Runs the refresh and rebuild every six hours and commits the result |
| `assets/` | CSS, JavaScript, self-hosted fonts and images |
| `ads.txt`, `robots.txt`, `manifest.webmanifest` | Served from the site root |

`_config.yml` keeps the docs, source fragments and scripts off the public site.

## Local preview

```bash
python3 build.py
python3 -m http.server 8000
```

## Day-to-day

- **Add or edit a platform:** change `data/gigs.json`, push. The workflow rebuilds the pages.
- **Write a guide:** add a fragment to `src/guides/` (copy an existing one), push.
- **Manual ad units:** paste slot IDs into `ad_slots` in `src/site.json`. Until then, AdSense Auto ads handle placement.
- **Force a data refresh:** Actions tab, "Auto-refresh content", Run workflow.

## Forms

Every form posts to FormSubmit. The destination inbox is assembled in the browser at send time and is not written anywhere in this repository. The first submission triggers a one-time activation email from FormSubmit to the inbox; click the link in it once and all forms start delivering.

## Custom domain

1. In the domain's DNS, add `A` records for `@` pointing to 185.199.108.153, 185.199.109.153, 185.199.110.153 and 185.199.111.153, and a `CNAME` for `www` pointing to `webworksa1.github.io`.
2. In the repository's Settings, Pages, enter `cash.work` as the custom domain and tick Enforce HTTPS.

## Data sources and credit

Remote jobs come from the public feeds of Remotive, Jobicy, Himalayas, Arbeitnow and Remote OK. Each listing links back to its original posting and the sources are credited on the jobs page. Videos are embedded from YouTube in privacy-enhanced mode. Headlines link to their publishers.

## Notice

Cash.Work is an independent publication and is not affiliated with any business using a similar name or with any platform it lists. Original text, design and code © Cash.Work. All rights reserved.
