# Cash.Work: phase-wise build prompt

A reusable, phase-by-phase prompt for building (or rebuilding) Cash.Work. Run each phase in order; each ends with a checkpoint that must pass before the next phase starts.

Placeholders: `OWNER_EMAIL` is the single inbox for every form (never written in plain text anywhere in the site or repo; assemble it at runtime from an encoded value). `OWNER_CONTACT_URL` is the owner's contact page used by the top-of-page banner.

---

## The concept (decided)

**Cash.Work: gigs, shifts and remote jobs ranked by how fast they pay.**

The domain reads as "work that pays cash". The site serves people who need income soon (gig workers, students, parents, career switchers, remote job seekers) and ranks every legit way to earn by payout speed first, then pay. Revenue comes from five streams:

1. Google AdSense on high-intent jobs and personal-finance content.
2. Worker lead generation: a matching quiz whose consented leads can be referred to gig platforms and staffing partners.
3. Employer lead generation: free, featured ($49) and partner (from $149/month) listings.
4. Sponsorships: directory features, sponsored guides, alert-email placements, contest sponsors.
5. Reader donations for operations, talent, promotion and contest prizes.

---

## Phase 1: Research and positioning

Prompt:
> Open and read at least 38 leading sites in the gig work, side hustle, remote jobs and earnings-calculator niche (marketplaces, job boards, gig app directories, personal finance publishers, calculators). For each, record what it does, its navigation, key features, forms and lead magnets, monetization and layout. Identify the gap Cash.Work can own. Output a research table and a one-paragraph positioning statement.

Checkpoint: research table with 38+ rows; a positioning that no competitor already owns (here: payout speed as the primary ranking axis).

## Phase 2: Information architecture and content model

Prompt:
> Define the sitemap and the data model for Cash.Work. Pages: home, gig directory, remote jobs, get matched (quiz), tools hub with five calculators, guides hub with at least eight long-form guides, videos, news, hire workers, advertise and partner, contests, careers, support (donations), about, contact, privacy, terms, disclaimers (with trademark and copyright notice), 404. Model each platform in `data/gigs.json` with: id, name, official URL, category, mode (local/remote), payout speed (instant, within days, weekly, after approval), typical gross pay range and note, requirements, car required, regions, summary.

Checkpoint: every page has a single job; every platform record has all fields; pay ranges are labelled gross and sourced.

## Phase 3: Design system

Prompt:
> Create a distinctive visual identity grounded in money paper: security-paper mint background, bank-ink navy text, banknote green actions, a stamp red used only for the PAID stamp. Display type: Archivo (variable width, expanded, heavy). Body: Public Sans. Self-host the fonts. The one memorable element is an interactive payday cheque in the hero that fills in an estimated amount, written-out words and a PAID stamp as the visitor chooses work type and hours. Use ledger-style ruled rows (not card grids) for directories and lists. Avoid template tells: no all-caps eyebrows, no middle-dot meta strings, no arrows appended to buttons. Responsive to 360px, visible focus, reduced motion respected.

Checkpoint: screenshots at desktop and mobile look intentional; contrast passes WCAG AA.

## Phase 4: Static build system and core pages

Prompt:
> Build a static site that runs on the GitHub Pages free plan from the main branch. Write page bodies as fragments in `src/` and a standard-library Python `build.py` that wraps them in a shared layout and writes finished HTML to the repo root, plus `sitemap.xml`. The layout must include on every page: the exact AdSense tag `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6620975821265271" crossorigin="anonymous"></script>` in the head; at the very top a full-width banner reading "Contact, if you are interested in this website/domain name/Sponsorship/Advertisement/Partnership" linked to OWNER_CONTACT_URL (the URL never shown as text); canonical, Open Graph and JSON-LD (WebSite, BreadcrumbList, Article, FAQPage where relevant); header nav with a "Get matched" button; footer with the independence, trademark and earnings notice. Prerender the gig directory, jobs, news and videos into the HTML so crawlers see real content.

Checkpoint: every built page has the AdSense tag and the banner; all internal links resolve; no page depends on JavaScript to show its main content.

## Phase 5: Interactive features

Prompt:
> Add vanilla JavaScript (no frameworks) for: (a) the hero cheque estimator with number-to-words; (b) directory search, filters (type, payout speed, in person or remote, country, no car), sorting and compare-up-to-three; (c) a remote jobs board that loads `data/jobs.json` with search, category, source, job type, salary-only filter and pagination; (d) five calculators: gig pay after costs and tax, hourly to salary both ways, freelance minimum rate, cash goal planner, job scam checker; (e) click-to-load YouTube embeds in privacy-enhanced mode.

Checkpoint: functional test of each feature in a headless browser with zero console errors.

## Phase 6: Lead generation, donations, contests, hiring, advertising

Prompt:
> Build a six-question matching quiz (timing, place, vehicle, skills, region, hours and goal) that scores every platform, shows the top three instantly and unlocks the full list and a printable 7-day plan with name, email, optional phone and explicit consent (including consent to be introduced to matching partners). Add forms for: fast-pay alerts, remote job alerts, employer requests (with honesty attestation), advertising and partnership enquiries, contest entries (with official rules, 18+, skill-testing question for Canada), talent applications, support pledges, platform suggestions, creator suggestions and contact. Send every form by AJAX to FormSubmit at OWNER_EMAIL, with the address assembled at runtime from an encoded value so it never appears in page source, plus a honeypot field. Donations open PayPal's donate page with the account built at click time; offer preset amounts, a custom amount and a monthly option, and publish how support is allocated (prizes, talent, operations, promotion).

Checkpoint: the plain-text address appears in no file in the repo; every form shows clear success and failure states.

## Phase 7: AdSense readiness and compliance

Prompt:
> Prepare for AdSense approval: substantial original content (8+ guides of 700 to 1,300 words, tool explanations, about page with research method), privacy policy with Google's required advertising-cookie disclosures and opt-out links, terms, disclaimers (earnings, affiliate, accuracy, trademark and copyright with independence from any similarly named business), contact page, `ads.txt` with `google.com, pub-6620975821265271, DIRECT, f08c47fec0942fa0`, `robots.txt`, sitemap. Rely on Auto ads until manual slot IDs exist; manual units are labelled "Advertisement" and kept away from buttons and forms. No get-rich-quick claims, no gambling, no pay-to-join offers.

Checkpoint: policy pages linked from every footer; no thin pages; ads.txt served at the root.

## Phase 8: Self-updating automation

Prompt:
> Write `scripts/fetch_data.py` (standard library only) that pulls remote jobs from Remotive (at most four calls a day), Jobicy, Himalayas, Arbeitnow and Remote OK; normalises, categorises and de-duplicates them; drops jobs older than 45 days; pulls the latest videos from a list of creator channels via YouTube RSS (resolving @handles to channel IDs); pulls work headlines from Google News RSS; keeps previous data for any source that fails; and writes `data/*.json` plus `meta.json`. Add a GitHub Actions workflow that runs every six hours, on manual dispatch and on source changes, then runs `build.py` and commits changed data and pages to main. Credit every job source with a link and honour Remote OK's followed-link requirement.

Checkpoint: workflow run succeeds; jobs, videos and news appear on the live site; sitemap lastmod updates.

## Phase 9: SEO, performance and accessibility

Prompt:
> Unique titles and descriptions per page, canonical URLs on the final domain, breadcrumb and article structured data, FAQ schema on the home page, Open Graph image, web manifest and icons, self-hosted fonts with preload, lazy-loaded images, no render-blocking third parties besides the AdSense loader, semantic headings, labelled form controls, skip link, keyboard-accessible quiz and filters.

Checkpoint: headless screenshots at 1366px and 390px; no layout overflow; all images have dimensions.

## Phase 10: Launch and growth

Prompt:
> Push to the main branch of the repository, enable GitHub Pages from main (root), run the refresh workflow once, then point the custom domain at GitHub Pages and enable HTTPS. Submit the sitemap to Google Search Console, apply to AdSense with the custom domain, turn on Google's consent message for EEA/UK visitors, and activate the form endpoint by confirming the first submission email. Growth backlog: programmatic city pages with live local data, a weekly fast-pay alert newsletter, sponsor-funded prize pools, and a two-sided shift marketplace once employer demand is proven.
