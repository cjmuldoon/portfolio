# LK Design and Build — SEO & Social Share Guidelines

Reference for anyone building or editing **lkdesignandbuild.com.au**.
Every rule here is load-bearing for organic traffic, Google Business Profile ranking, and how the site looks when someone drops a link into Messages / WhatsApp / LinkedIn.

> **TL;DR** — use the example meta tag block in §5 on every page, swap in a page-specific title / description / OG image, keep titles under 60 characters, keep descriptions under 160, give every non-decorative image an alt attribute, and make sure phone number + email + address are byte-identical across the website, Google Business Profile, and directory citations.

---

## 1. Business context

| | |
|---|---|
| Domain | `lkdesignandbuild.com.au` |
| Business name | LK Design and Build |
| Principal | Lyda |
| Email | `lyda@lkdesignandbuild.com.au` |
| Phone | `+61 401 061 246` |
| Location | Adelaide, South Australia |
| Service area | Adelaide metro + Adelaide Hills |
| Segment | Premium home renovations, additions, custom new builds |
| Slogan | *Considered design. Precision build.* |

### 1.1 Target keyword clusters
Rank for a **tight Adelaide cluster** rather than broad terms.

- **Primary** — `Adelaide builder`, `home renovation Adelaide`, `custom home builder Adelaide`, `Adelaide design and build`
- **Secondary** — `luxury home renovation Adelaide`, `Adelaide home extension`, `heritage renovation Adelaide`, `knock-down rebuild Adelaide`
- **Suburb-modified** (one landing page each as you grow) — `{suburb} renovation builder` for Unley, Norwood, Burnside, Walkerville, North Adelaide, Glenelg, Prospect, Mitcham
- **Long-tail commercial** — `cost of home renovation Adelaide`, `how to choose a builder Adelaide`

Avoid competing nationally (`luxury builder Australia`) — it's a losing fight against volume spend.

---

## 2. On-page SEO

### 2.1 Title tags — 50–60 chars

Format: `{Page Topic + primary keyword} | LK Design and Build` or `{Page Topic} — {Modifier} | LK Design and Build`.

| Page | Title |
|---|---|
| Home | `LK Design and Build — Premium Home Renovations, Adelaide` |
| Services | `Renovations, Additions & New Builds in Adelaide — LK Design and Build` |
| Projects | `Featured Projects — Adelaide Renovations & Builds` |
| About | `About Lyda — LK Design and Build, Adelaide` |
| Contact | `Contact — LK Design and Build, Adelaide` |

### 2.2 Meta descriptions — 150–160 chars

Write for **click-through**, not keyword density. Use active voice and a call to act.

- Home: *Premium home renovations, additions and custom builds across Adelaide. Considered design. Precision build. Talk to Lyda about your next project.*
- Services: *Heritage renovations, contemporary extensions and ground-up new builds in Adelaide. Every project led end-to-end by Lyda.*

### 2.3 Heading hierarchy

- Exactly **one `<h1>`** per page, containing the primary keyword.
- `<h2>` for major sections, `<h3>` for sub-sections. Never skip levels.
- Don't style non-heading text as a heading — use CSS on a `<p>` instead, otherwise Google interprets it as structure.

### 2.4 Image alt text

- **Every non-decorative image** must have an `alt`. Purely decorative? Use `alt=""` (not missing — `alt=""` tells screen readers to skip).
- Describe the *subject*, not the filename. Include location / materials when relevant.
  - Good: `alt="Stone Hills Road extension — blackbutt cladding and raw concrete entry"`
  - Bad: `alt="IMG_4512"`
- Never stuff keywords into alt — it's an accessibility tag first, SEO second.

### 2.5 Internal linking

- Every page should link **into** at least two other pages.
- Project pages cross-link to relevant service pages.
- Breadcrumbs (`Home → Projects → Unley Extension`) everywhere except the home page.

---

## 3. Technical SEO

### 3.1 URLs

- Lowercase, hyphenated, no trailing params: `/projects/unley-extension/` not `/Projects/Unley_Extension.html`.
- Trailing slash convention must be consistent — pick one and 301 the other.

### 3.2 Canonicals

Every page has a self-referencing canonical:

```html
<link rel="canonical" href="https://lkdesignandbuild.com.au/services/renovations/">
```

### 3.3 robots.txt

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /cart/
Sitemap: https://lkdesignandbuild.com.au/sitemap.xml
```

### 3.4 sitemap.xml

Auto-generate on build. Include every public page with `<lastmod>`. Submit once to Google Search Console; re-submission is only needed when URLs move.

### 3.5 HTTPS + HSTS

Force HTTPS, set `Strict-Transport-Security: max-age=31536000; includeSubDomains`.

### 3.6 Core Web Vitals targets

| Metric | Target | Primary lever |
|---|---|---|
| **LCP** (largest contentful paint) | < 2.5s | Hero image priority + `<link rel="preload">`; compressed WebP/AVIF |
| **INP** (interaction to next paint) | < 200ms | Defer non-critical JS; avoid heavy event handlers on scroll |
| **CLS** (cumulative layout shift) | < 0.1 | Explicit `width` / `height` on every `<img>`; reserve space for embeds |

### 3.7 Images

- Export **WebP or AVIF** as primary, JPG fallback.
- Hero: ≤ 200 KB at 2× resolution, lazy-load everything below the fold (`loading="lazy"`).
- Always set `width` and `height` attributes.
- Serve responsive images with `srcset` at 1×/2× densities.

### 3.8 Fonts

- Inter + Courier New (system). Preload Inter weights you actually use:
  ```html
  <link rel="preload" href="/fonts/Inter-Regular.woff2" as="font" type="font/woff2" crossorigin>
  ```
- `font-display: swap;` on every `@font-face` to eliminate FOIT.

---

## 4. Structured data (Schema.org JSON-LD)

Inject on every page in `<head>`. At minimum, Organization sitewide + LocalBusiness on the home / contact page.

### 4.1 LocalBusiness / GeneralContractor (home + contact page)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "GeneralContractor",
  "name": "LK Design and Build",
  "legalName": "LK Design and Build",
  "url": "https://lkdesignandbuild.com.au",
  "logo": "https://lkdesignandbuild.com.au/assets/branding/final/lk-logo-champagne.svg",
  "image": "https://lkdesignandbuild.com.au/assets/branding/final/og-image.jpg",
  "telephone": "+61401061246",
  "email": "lyda@lkdesignandbuild.com.au",
  "priceRange": "$$$",
  "slogan": "Considered design. Precision build.",
  "founder": { "@type": "Person", "name": "Lyda" },
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Adelaide",
    "addressRegion": "SA",
    "addressCountry": "AU"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": -34.9285,
    "longitude": 138.6007
  },
  "areaServed": [
    { "@type": "City", "name": "Adelaide" },
    { "@type": "AdministrativeArea", "name": "Adelaide Hills" }
  ],
  "sameAs": [
    "https://www.instagram.com/lkdesignandbuild",
    "https://www.linkedin.com/company/lk-design-and-build"
  ]
}
</script>
```

### 4.2 BreadcrumbList (interior pages)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://lkdesignandbuild.com.au/" },
    { "@type": "ListItem", "position": 2, "name": "Projects", "item": "https://lkdesignandbuild.com.au/projects/" },
    { "@type": "ListItem", "position": 3, "name": "Unley Extension" }
  ]
}
</script>
```

### 4.3 Project pages — `Project` / `CreativeWork`

Use `Project` with `@type` `"HomeAndConstructionBusiness"` where the project has verifiable details (location, completion date, photo credits).

---

## 5. Open Graph + Twitter Cards (social sharing)

**Paste this block into every page's `<head>`** — only the `title`, `description`, `url`, and (optionally) `image` lines need per-page tweaks.

```html
<!-- Primary -->
<meta name="description" content="{page description, 150–160 chars}">
<link rel="canonical" href="https://lkdesignandbuild.com.au/{path}/">

<!-- Open Graph -->
<meta property="og:site_name" content="LK Design and Build">
<meta property="og:type" content="website">
<meta property="og:locale" content="en_AU">
<meta property="og:url" content="https://lkdesignandbuild.com.au/{path}/">
<meta property="og:title" content="{page title}">
<meta property="og:description" content="{page description}">
<meta property="og:image" content="https://lkdesignandbuild.com.au/assets/branding/final/og-image.jpg">
<meta property="og:image:secure_url" content="https://lkdesignandbuild.com.au/assets/branding/final/og-image.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="LK Design and Build — Adelaide premium renovations and builds">

<!-- Twitter / X -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{page title}">
<meta name="twitter:description" content="{page description}">
<meta name="twitter:image" content="https://lkdesignandbuild.com.au/assets/branding/final/og-image.jpg">
<meta name="twitter:image:alt" content="LK Design and Build — Adelaide premium renovations and builds">
```

### 5.1 OG image — spec & rules

| Spec | Value |
|---|---|
| Dimensions | **1200 × 630 px** (aspect 1.91:1) |
| Format | JPG preferred (smaller); PNG if transparency/text sharpness matters |
| File size | **< 300 KB** ideally (LinkedIn aggressively rejects > 5 MB) |
| Colour space | sRGB |
| Safe area | Keep all critical content inside **centre 600 × 600 px** — Facebook/iMessage crop to square on mobile |
| Text size | Minimum 24 px body text, 48 px+ for wordmarks — it has to read at ~400 px wide in a chat thread |
| Bleed | Add 20 px padding away from every edge — avoids text being cropped when Slack/Discord trim the frame |
| Accessibility | No critical info in colour alone; include a text `og:image:alt` |

**Starter asset**: [`/assets/branding/final/og-image.jpg`](../og-image.jpg) — regenerated from `og-image.svg`. Use this for the home page and any page that doesn't warrant a custom hero.

### 5.2 Per-page OG image overrides

Where a page has a strong hero photograph, generate a page-specific OG image:

- **Home** → default `og-image.jpg`
- **Projects index** → `og-image-projects.jpg` (grid collage)
- **Individual project** → `og-image-project-{slug}.jpg` — hero photo of the build with a small LK lockup overlayed bottom-right
- **Blog / journal** → `og-image-blog-{slug}.jpg` — feature image
- **Contact / About** → default `og-image.jpg`

Workflow for project OG images:

1. Export landscape hero at 1600 × 840, downscale with a slight blur + 10% darken on bottom 20% band.
2. Overlay lk-logo-horizontal-champagne.svg (height 48px) in bottom-right with 40px margin.
3. Export JPG, quality 85, target ≤ 280 KB.

### 5.3 Validation

After deploying, validate share previews **before** posting:

- Facebook → [Sharing Debugger](https://developers.facebook.com/tools/debug/)
- LinkedIn → [Post Inspector](https://www.linkedin.com/post-inspector/)
- X / Twitter → [Card Validator](https://cards-dev.twitter.com/validator) (legacy — works for preview only)
- Schema/JSON-LD → [Rich Results Test](https://search.google.com/test/rich-results)

Cache-bust on re-upload by appending `?v=2` to the image URL — Facebook aggressively caches OG images.

---

## 6. Favicons & device icons

Put these in `/` (site root) for broad client support:

```html
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/svg+xml" href="/assets/branding/final/lk-icon-champagne.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0A0A0A">
```

- `favicon.ico` — multi-resolution 16/32/48 px, generated from `lk-icon-champagne.svg`.
- `apple-touch-icon.png` — 180 × 180 px, **on a solid `#0A0A0A` background** (Apple clips transparency).
- `site.webmanifest` — for PWA install / Android home screen.

---

## 7. Local SEO

### 7.1 Google Business Profile

Non-negotiable, highest-ROI action. When setting it up:

- **Category** — primary `General Contractor`; secondary `Home Builder`, `Remodeler`, `Construction Company`.
- **Service area** — Adelaide + every suburb you'll service (Burnside, Mitcham, Unley, Norwood, Walkerville, North Adelaide, Prospect, Glenelg, Brighton, plus the Adelaide Hills townships).
- **Services** — list each service explicitly with its own short description (Google uses these as local ranking signals).
- **Hours** — fill them in even if "by appointment". Empty = algorithmic penalty.
- **Photos** — upload minimum 10 at launch, then at least one new photo per month. Include exterior, interior, progress shots, and a portrait of Lyda. Geotag if possible.
- **Reviews** — reply to every one, good or bad, within 48 hours. Aim for 10 reviews in the first 90 days.
- **Posts** — minimum one Google Post per fortnight (new project, seasonal tip, availability update).

### 7.2 NAP consistency

Name, Address, Phone must be **identical** across the website, Google Business Profile, and every directory:

- Name → `LK Design and Build` (no "Pty Ltd", no "& Build", no "and Build Pty Ltd" — just this)
- Address → `Adelaide, South Australia` (or the full PO Box if you have one — just pick one and stick)
- Phone → `0401 061 246` (domestic format) / `+61 401 061 246` (international schema)
- Email → `lyda@lkdesignandbuild.com.au`

### 7.3 Priority directories (AU-specific)

1. Google Business Profile
2. Bing Places
3. Apple Maps / Apple Business Connect
4. [Houzz](https://www.houzz.com.au/) — highest intent for AU renovations; worth a paid Houzz Pro+ subscription
5. HIA member listing (if HIA member)
6. [TrueLocal](https://www.truelocal.com.au/)
7. Yellow Pages Australia
8. [Hipages](https://hipages.com.au/) — lead-gen, paid
9. LocalSearch.com.au

---

## 8. Content strategy

### 8.1 Foundational pages (ship with launch)

- Home
- Services — Renovations / Additions & Extensions / New Builds / Heritage / Consulting
- Projects index + individual project case studies (minimum 4 at launch, 1 new per month)
- About Lyda
- Process (from first conversation → handover)
- Contact

### 8.2 Growth content

- Suburb landing pages — one `/renovation-builder/{suburb}/` page per priority suburb, ~800 words, with a real completed project from that area.
- Journal / blog — seasonal long-form: *"Planning a 2026 Adelaide home extension: lead times, council approvals, and what drives cost"*.
- Guide pages — *"Heritage overlay rules in Unley: what you can and can't change"*, *"Adelaide double-brick renovation: what to expect"*. These rank extremely well for commercial long-tail.

### 8.3 Don't

- Don't duplicate suburb pages with just a find-and-replace on the suburb name. Google identifies and de-indexes doorway pages.
- Don't buy backlinks. The penalty cost outweighs any gain.
- Don't use AI-generated text as-is — rewrite so it reads in Lyda's voice.

---

## 9. Analytics & monitoring

### 9.1 Install

- **Google Search Console** — verify via DNS TXT record. Submit sitemap. Check weekly for coverage errors and manual actions.
- **Google Analytics 4** — configure with these conversion events:
  - `phone_click` (tap-to-call)
  - `email_click` (mailto link)
  - `form_submit` (contact form success)
  - `download` (stationery or asset download from hub)
- **Microsoft Clarity** (free) — heatmaps + session recordings. Watch the first 100 sessions closely to spot friction on the contact flow.

### 9.2 Targets (first 12 months)

| Metric | 3 months | 12 months |
|---|---|---|
| Indexed pages | ≥ 20 | ≥ 60 |
| Organic sessions / month | 200 | 1,500 |
| GBP profile views / month | 500 | 3,000 |
| Enquiry form submissions / month | 4 | 20 |

### 9.3 Review cadence

- **Weekly** — Search Console errors, GBP messages/reviews.
- **Monthly** — keyword position report, GA4 conversion funnel.
- **Quarterly** — content gap analysis, competitor backlink review, site-wide Lighthouse audit.

---

## 10. Pre-launch checklist

Tick every box before pointing DNS at production.

- [ ] HTTPS + HSTS active
- [ ] Every page has unique title + meta description
- [ ] Canonical on every page
- [ ] `robots.txt` live; `sitemap.xml` submitted to Search Console
- [ ] LocalBusiness JSON-LD on home + contact
- [ ] OG tags tested in Facebook Debugger + LinkedIn Post Inspector
- [ ] Favicon + apple-touch-icon + manifest in place
- [ ] All images have alt text
- [ ] Lighthouse ≥ 90 on Performance, Accessibility, SEO (mobile)
- [ ] Google Business Profile published + verified
- [ ] GA4 + Search Console verified and receiving data
- [ ] 404 page ships and returns HTTP 404 (not 200)
- [ ] `noindex` removed from production build
