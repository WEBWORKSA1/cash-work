#!/usr/bin/env python3
"""Refresh Cash.Work's live data: remote jobs, YouTube videos and work news.

Runs in GitHub Actions every six hours (standard library only). If a source
fails, the previous data for that source is kept, so the site never empties.
Sources and their terms:
  Remotive   https://remotive.com/api/remote-jobs   link back + credit; max ~4 calls/day
  Jobicy     https://jobicy.com/api/v2/remote-jobs  credit
  Himalayas  https://himalayas.app/jobs/api         credit with a link
  Arbeitnow  https://www.arbeitnow.com/api/job-board-api  link back
  Remote OK  https://remoteok.com/api              followed link back + credit
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = "Mozilla/5.0 (compatible; CashWorkRefresher/1.0; +https://cash.work/about.html)"
NOW = dt.datetime.now(dt.timezone.utc)
MAX_AGE_DAYS = 45
MAX_JOBS = 450

YOUTUBE_CHANNELS = [
    # (label, channel id or @handle). Handles are resolved to channel IDs at run time.
    ("The Rideshare Guy", "UCCwyU2RqlalzpKIrUhYWHfw"),
    ("Upwork", "@Upwork"),
    ("Fiverr", "@fiverr"),
    ("NerdWallet", "@NerdWallet"),
    ("Graham Stephan", "@GrahamStephan"),
    ("Ali Abdaal", "@aliabdaal"),
    ("Mark Tilbury", "@marktilbury"),
]
NEWS_QUERIES = ['"gig economy"', '"gig workers"', '"side hustle" income', '"remote jobs" OR "remote work" hiring', 'freelancers earnings']
NEWS_MUST = re.compile(r"gig|side hustle|side income|freelanc|remote (?:work|job)|job|hiring|worker|wage|pay|salary|income|earn|uber|lyft|doordash|instacart|delivery|rideshare|employ|career|labou?r|contractor", re.I)
NEWS_SKIP = re.compile(r"\b(?:cast|movie|film|drama|series|trailer|album|song|thieves|murder|killed|arrested|obituary)\b", re.I)


def log(msg: str) -> None:
    print(f"[refresh] {msg}", flush=True)


def get(url: str, accept: str = "application/json", tries: int = 2) -> bytes:
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept, "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - network errors of many kinds
            last = e
            time.sleep(2 + attempt * 3)
    raise RuntimeError(f"{url}: {last}")


def get_json(url: str):
    return json.loads(get(url).decode("utf-8", "replace"))


def load(name: str, default):
    p = DATA / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def save(name: str, obj) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


TAG_RE = re.compile(r"<[^>]+>")


def clean(s, limit: int = 140) -> str:
    s = html.unescape(TAG_RE.sub(" ", str(s or "")))
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


def to_iso(value) -> str:
    if value in (None, ""):
        return NOW.isoformat()
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            v = float(value)
            if v > 1e12:
                v /= 1000
            return dt.datetime.fromtimestamp(v, dt.timezone.utc).isoformat()
        s = str(value).replace("Z", "+00:00")
        d = dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc).isoformat()
    except Exception:  # noqa: BLE001
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(str(value)).astimezone(dt.timezone.utc).isoformat()
        except Exception:  # noqa: BLE001
            return NOW.isoformat()


def money_range(lo, hi, cur="USD", period="") -> str:
    if not period:
        try:
            top = max(float(lo or 0), float(hi or 0))
        except (TypeError, ValueError):
            top = 0
        # Some feeds give hourly or monthly figures in the same fields as annual ones.
        period = "hr" if 0 < top < 300 else ("mo" if 0 < top < 20000 else "yr")

    def f(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if v <= 0:
            return None
        return f"{v/1000:.0f}k" if v >= 1000 else f"{v:.0f}"
    a, b = f(lo), f(hi)
    sym = "$" if (cur or "USD").upper() in ("USD", "CAD", "AUD") else ((cur or "").upper() + " ")
    if a and b and a != b:
        return f"{sym}{a}–{b}/{period}"
    if a or b:
        return f"{sym}{a or b}/{period}"
    return ""


CATS = [
    ("Software and IT", r"software|developer|engineer|devops|backend|front[- ]?end|full[- ]?stack|programm|qa |sre|cloud|security|it support|sysadmin"),
    ("Data and AI", r"data|analyt|machine learning|\bml\b|\bai\b|scientist"),
    ("Customer support", r"support|customer|success|service rep|help ?desk"),
    ("Sales", r"sales|account exec|business develop|\bsdr\b|\bbdr\b"),
    ("Marketing", r"marketing|seo|growth|social media|content market|brand|pr "),
    ("Writing and content", r"writ|editor|copy|content|translat|transcri"),
    ("Design", r"design|ux|ui |product designer|graphic|illustrat"),
    ("Product and project", r"product manager|project|program manager|scrum|product owner"),
    ("Finance and legal", r"financ|account|bookkeep|legal|lawyer|paralegal|tax|payroll"),
    ("HR and recruiting", r"recruit|talent|\bhr\b|human resources|people ops"),
    ("Admin and operations", r"admin|assistant|operations|virtual assistant|data entry|coordinator"),
    ("Education", r"teach|tutor|instructor|curriculum|education"),
    ("Healthcare", r"nurse|health|medical|clinical|therap|pharm"),
]


def categorize(*texts) -> str:
    blob = " ".join(str(t or "") for t in texts).lower()
    for name, pat in CATS:
        if re.search(pat, blob):
            return name
    return "Other"


def norm_type(t) -> str:
    if isinstance(t, list):
        t = t[0] if t else ""
    t = str(t or "").replace("_", " ").replace("-", " ").strip().lower()
    for k, v in (("full", "Full-time"), ("part", "Part-time"), ("contract", "Contract"), ("freelance", "Freelance"), ("intern", "Internship"), ("temp", "Temporary")):
        if k in t:
            return v
    return t.title() if t else ""


# ---------------------------------------------------------------- job sources
def src_remotive():
    d = get_json("https://remotive.com/api/remote-jobs?limit=150")
    out = []
    for j in d.get("jobs", []):
        out.append({
            "id": f"remotive-{j.get('id')}", "title": clean(j.get("title")), "company": clean(j.get("company_name"), 80),
            "url": j.get("url"), "source": "Remotive", "type": norm_type(j.get("job_type")),
            "location": clean(j.get("candidate_required_location"), 60) or "Remote",
            "salary": clean(j.get("salary"), 40), "date": to_iso(j.get("publication_date")),
            "category": categorize(j.get("category"), j.get("title")), "tags": [clean(t, 30) for t in (j.get("tags") or [])[:5]],
        })
    return out


def src_jobicy():
    d = get_json("https://jobicy.com/api/v2/remote-jobs?count=100")
    out = []
    for j in d.get("jobs", []):
        ind = j.get("jobIndustry")
        ind = ind[0] if isinstance(ind, list) and ind else ind
        out.append({
            "id": f"jobicy-{j.get('id')}", "title": clean(j.get("jobTitle")), "company": clean(j.get("companyName"), 80),
            "url": j.get("url"), "source": "Jobicy", "type": norm_type(j.get("jobType")),
            "location": clean(j.get("jobGeo"), 60) or "Remote",
            "salary": money_range(j.get("annualSalaryMin"), j.get("annualSalaryMax"), j.get("salaryCurrency") or "USD"),
            "date": to_iso(j.get("pubDate")), "category": categorize(html.unescape(str(ind or "")), j.get("jobTitle")), "tags": [],
        })
    return out


def src_himalayas():
    out = []
    for offset in range(0, 100, 20):
        d = get_json(f"https://himalayas.app/jobs/api?limit=20&offset={offset}")
        jobs = d.get("jobs", []) if isinstance(d, dict) else []
        if not jobs:
            break
        for j in jobs:
            locs = j.get("locationRestrictions") or []
            loc = ", ".join(clean(x if isinstance(x, str) else (x.get("name") if isinstance(x, dict) else ""), 30) for x in locs[:3]) or "Worldwide"
            cats = j.get("categories") or j.get("parentCategories") or []
            out.append({
                "id": f"himalayas-{j.get('guid') or j.get('applicationLink')}", "title": clean(j.get("title")),
                "company": clean(j.get("companyName"), 80), "url": j.get("applicationLink") or j.get("guid"),
                "source": "Himalayas", "type": norm_type(j.get("employmentType")), "location": loc,
                "salary": money_range(j.get("minSalary"), j.get("maxSalary"), j.get("currency") or j.get("salaryCurrency") or "USD"),
                "date": to_iso(j.get("pubDate") or j.get("publishedAt")),
                "category": categorize(" ".join(map(str, cats)), j.get("title")), "tags": [],
            })
        time.sleep(1.5)
    return out


def src_arbeitnow():
    out = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    for _ in range(3):
        d = get_json(url)
        for j in d.get("data", []):
            if not j.get("remote"):
                continue
            out.append({
                "id": f"arbeitnow-{j.get('slug')}", "title": clean(j.get("title")), "company": clean(j.get("company_name"), 80),
                "url": j.get("url"), "source": "Arbeitnow", "type": norm_type(j.get("job_types")),
                "location": "Remote" + (f" ({clean(j.get('location'), 40)})" if j.get("location") else ""),
                "salary": "", "date": to_iso(j.get("created_at")),
                "category": categorize(" ".join(j.get("tags") or []), j.get("title")), "tags": [clean(t, 30) for t in (j.get("tags") or [])[:5]],
            })
        nxt = (d.get("links") or {}).get("next")
        if not nxt:
            break
        url = nxt
        time.sleep(1.5)
    return out


def src_remoteok():
    d = get_json("https://remoteok.com/api")
    out = []
    for j in d[1:] if isinstance(d, list) else []:
        if not isinstance(j, dict) or not j.get("position"):
            continue
        out.append({
            "id": f"remoteok-{j.get('id')}", "title": clean(j.get("position")), "company": clean(j.get("company"), 80),
            "url": j.get("url") or f"https://remoteok.com/remote-jobs/{j.get('id')}", "source": "Remote OK",
            "type": "", "location": clean(j.get("location"), 60) or "Remote",
            "salary": money_range(j.get("salary_min"), j.get("salary_max")), "date": to_iso(j.get("date") or j.get("epoch")),
            "category": categorize(" ".join(j.get("tags") or []), j.get("position")), "tags": [clean(t, 30) for t in (j.get("tags") or [])[:5]],
        })
    return out


SOURCES = [
    ("Remotive", src_remotive, 5.5),  # hours between calls (Remotive asks for at most four a day)
    ("Jobicy", src_jobicy, 0),
    ("Himalayas", src_himalayas, 0),
    ("Arbeitnow", src_arbeitnow, 0),
    ("Remote OK", src_remoteok, 0),
]


def refresh_jobs(meta: dict) -> list:
    old = load("jobs.json", {"jobs": []}).get("jobs", [])
    status = meta.setdefault("sources", {})
    jobs = []
    for name, fn, min_gap in SOURCES:
        prev = [j for j in old if j.get("source") == name]
        last = status.get(name, {}).get("fetched")
        if min_gap and last:
            age_h = (NOW - dt.datetime.fromisoformat(last)).total_seconds() / 3600
            if age_h < min_gap:
                log(f"{name}: skipped (fetched {age_h:.1f}h ago), keeping {len(prev)}")
                jobs.extend(prev)
                continue
        try:
            got = [j for j in fn() if j.get("title") and j.get("url", "").startswith("http")]
            if not got:
                raise RuntimeError("no jobs returned")
            jobs.extend(got)
            status[name] = {"ok": True, "count": len(got), "fetched": NOW.isoformat()}
            log(f"{name}: {len(got)} jobs")
        except Exception as e:  # noqa: BLE001
            jobs.extend(prev)
            status[name] = {**status.get(name, {}), "ok": False, "error": str(e)[:200], "tried": NOW.isoformat()}
            log(f"{name}: FAILED ({e}); keeping {len(prev)} previous")
    cutoff = NOW - dt.timedelta(days=MAX_AGE_DAYS)
    seen, out = set(), []
    for j in sorted(jobs, key=lambda x: x.get("date", ""), reverse=True):
        key = (j["title"].lower(), (j.get("company") or "").lower())
        if key in seen:
            continue
        try:
            if dt.datetime.fromisoformat(j["date"]) < cutoff:
                continue
        except Exception:  # noqa: BLE001
            pass
        seen.add(key)
        out.append(j)
    return out[:MAX_JOBS]


# ---------------------------------------------------------------- videos
ATOM = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}


def resolve_channel(handle: str, cache: dict) -> str | None:
    if handle.startswith("UC"):
        return handle
    if handle in cache:
        return cache[handle]
    try:
        page = get("https://www.youtube.com/" + handle, accept="text/html").decode("utf-8", "replace")
        m = re.search(r'"externalId":"(UC[\w-]{22})"', page) or re.search(r'<meta itemprop="identifier" content="(UC[\w-]{22})"', page) \
            or re.search(r'"channelId":"(UC[\w-]{22})"', page)
        if m:
            cache[handle] = m.group(1)
            return m.group(1)
    except Exception as e:  # noqa: BLE001
        log(f"YouTube {handle}: could not resolve ({e})")
    return None


def refresh_videos(meta: dict) -> list:
    old = load("videos.json", {"videos": []}).get("videos", [])
    cache = meta.setdefault("youtube_ids", {})
    videos = []
    for label, ref in YOUTUBE_CHANNELS:
        cid = resolve_channel(ref, cache)
        if not cid:
            videos.extend(v for v in old if v.get("channel") == label)
            continue
        try:
            root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", accept="application/atom+xml"))
            n = 0
            for e in root.findall("a:entry", ATOM):
                vid = e.findtext("yt:videoId", namespaces=ATOM)
                title = e.findtext("a:title", namespaces=ATOM)
                link = (e.find("a:link", ATOM).attrib.get("href", "") if e.find("a:link", ATOM) is not None else "")
                if not vid or "/shorts/" in link:
                    continue
                videos.append({"id": vid, "title": clean(title, 110), "channel": label, "date": to_iso(e.findtext("a:published", namespaces=ATOM))})
                n += 1
                if n >= 5:
                    break
            log(f"YouTube {label}: {n} videos")
        except Exception as e:  # noqa: BLE001
            videos.extend(v for v in old if v.get("channel") == label)
            log(f"YouTube {label}: FAILED ({e})")
        time.sleep(1)
    videos.sort(key=lambda v: v.get("date", ""), reverse=True)
    seen, out = set(), []
    for v in videos:
        if v["id"] not in seen:
            seen.add(v["id"])
            out.append(v)
    return out[:40] if out else old


# ---------------------------------------------------------------- news
def refresh_news() -> list:
    old = load("news.json", {"items": []}).get("items", [])
    items = []
    for q in NEWS_QUERIES:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + " when:7d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
        try:
            root = ET.fromstring(get(url, accept="application/rss+xml"))
            for it in root.iter("item"):
                title = it.findtext("title") or ""
                src = it.findtext("source") or ""
                if src and title.endswith(" - " + src):
                    title = title[: -len(src) - 3]
                items.append({"title": clean(title, 160), "url": it.findtext("link"), "source": clean(src, 60), "date": to_iso(it.findtext("pubDate"))})
            log(f"News '{q}': ok")
        except Exception as e:  # noqa: BLE001
            log(f"News '{q}': FAILED ({e})")
        time.sleep(1)
    if not items:
        return old
    items.sort(key=lambda x: x["date"], reverse=True)
    seen, out = set(), []
    for n in items:
        k = re.sub(r"\W+", "", n["title"].lower())[:60]
        if not NEWS_MUST.search(n["title"]) or NEWS_SKIP.search(n["title"]):
            continue
        if k and k not in seen and n.get("url"):
            seen.add(k)
            out.append(n)
    return out[:60]


def main() -> int:
    DATA.mkdir(exist_ok=True)
    meta = load("meta.json", {})
    jobs = refresh_jobs(meta)
    save("jobs.json", {"updated": NOW.isoformat(), "count": len(jobs), "jobs": jobs})
    videos = refresh_videos(meta)
    save("videos.json", {"updated": NOW.isoformat(), "videos": videos})
    news = refresh_news()
    save("news.json", {"updated": NOW.isoformat(), "items": news})
    meta.update({"updated": NOW.isoformat(), "jobs": len(jobs), "videos": len(videos), "news": len(news)})
    save("meta.json", meta)
    log(f"done: {len(jobs)} jobs, {len(videos)} videos, {len(news)} headlines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
