#!/usr/bin/env python3
"""Generate the SEO / answer-engine pages for the portfolio. Standard library only.

Source of truth (edit these, then run `python scripts/build.py`):
  content/site.json    name, role, links, facts, "updated" date
  content/posts.json   the essays
  content/faq.json     the FAQ (shown on the page and published as FAQPage data)

Generated:
  v2/writing/index.html and v2/writing/<slug>/index.html   one real page per essay
  v2/sitemap.xml, v2/robots.txt, v2/llms.txt, v2/llms-full.txt
  and the regions of v2/index.html between the <!--NAME:START--> / <!--NAME:END-->
  markers (structured data, post cards, FAQ, post data for the in-page reader).

`--check` writes nothing and exits 1 if any generated file is out of date.
The literal text __SITE_URL__ is replaced with the real address at deploy time.
"""
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = os.path.join(ROOT, "v2")
CHECK = "--check" in sys.argv
TOKEN = "__SITE_URL__"

site = json.load(open(os.path.join(ROOT, "content", "site.json"), encoding="utf8"))
posts = json.load(open(os.path.join(ROOT, "content", "posts.json"), encoding="utf8"))
faq = json.load(open(os.path.join(ROOT, "content", "faq.json"), encoding="utf8"))

NAME = site["name"]
BASE = TOKEN
PERSON_ID = f"{BASE}/#person"
OG_IMAGE = f"{BASE}/assets/og-image.png"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
FONT_URL = "https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800&family=Instrument+Serif:ital@0;1&display=swap"

THEME_INIT = '<script>(function(){var t;try{t=localStorage.getItem("theme")}catch(e){}if(t!=="light"&&t!=="dark"){t=window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches?"light":"dark"}document.documentElement.setAttribute("data-theme",t)})()</script>\n'
THEME_BTN = ('<button class="theme-btn" id="themeBtn" type="button" aria-label="Switch to light theme" aria-pressed="false" title="Switch theme">'
             '<svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
             '<svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/></svg></button>')
THEME_JS = '<script>(function(){var b=document.getElementById("themeBtn"),r=document.documentElement,m=document.querySelector(\'meta[name="theme-color"]\');function a(t,s){r.setAttribute("data-theme",t);if(m)m.content=t==="light"?"#f7f6f2":"#06070a";b.setAttribute("aria-label",t==="light"?"Switch to dark theme":"Switch to light theme");b.setAttribute("aria-pressed",String(t==="light"));if(s){try{localStorage.setItem("theme",t)}catch(e){}}}b.onclick=function(){a(r.getAttribute("data-theme")==="light"?"dark":"light",true)};a(r.getAttribute("data-theme")||"dark")})()</script>'

stale = []  # files that differ from what we would write


# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(s, quote=True)


def plain(h):
    h = re.sub(r"<svg[\s\S]*?</svg>", " ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h)).strip()


def clip(s, n=158):
    s = plain(s)
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def js_json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def write(rel, content):
    path = os.path.join(ROOT, rel)
    content = content.replace("\r\n", "\n")
    old = open(path, encoding="utf8", newline="").read() if os.path.exists(path) else None
    if old == content:
        return
    stale.append(rel)
    if CHECK:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf8", newline="\n").write(content)


def swap(src, start, end, inner):
    i, j = src.index(start) + len(start), src.index(end)
    return src[:i] + inner + src[j:]


def nice_date(iso):
    y, m = iso.split("-")[:2]
    return f"{MONTHS[int(m) - 1][:3]} {y}"


# ---------------------------------------------------------------- structured data
def person_node(full=True):
    n = {"@type": "Person", "@id": PERSON_ID, "name": NAME, "url": f"{BASE}/", "sameAs": site["sameAs"]}
    if full:
        n.update({
            "alternateName": site["alternateName"],
            "image": f"{BASE}/assets/profile.webp",
            "jobTitle": site["jobTitle"],
            "description": site["summary"],
            "address": {"@type": "PostalAddress", "addressLocality": site["locality"], "addressCountry": site["country"]},
            "worksFor": {"@type": "Organization", "name": site["worksFor"]},
            "alumniOf": {"@type": "CollegeOrUniversity", "name": site["alumniOf"]},
            "knowsAbout": site["knowsAbout"],
        })
    return n


def home_graph():
    post_nodes = [{"@type": "BlogPosting", "@id": f"{BASE}/writing/{p['slug']}/#article", "headline": p["title"],
                   "url": f"{BASE}/writing/{p['slug']}/", "datePublished": p["iso"], "author": {"@id": PERSON_ID}} for p in posts]
    return {"@context": "https://schema.org", "@graph": [
        person_node(),
        {"@type": "WebSite", "@id": f"{BASE}/#website", "url": f"{BASE}/", "name": f"{NAME} - {site['jobTitle']}",
         "inLanguage": "en", "author": {"@id": PERSON_ID}, "publisher": {"@id": PERSON_ID}},
        {"@type": "ProfilePage", "@id": f"{BASE}/#profilepage", "url": f"{BASE}/", "name": f"{NAME} - {site['jobTitle']}",
         "inLanguage": "en", "isPartOf": {"@id": f"{BASE}/#website"}, "about": {"@id": PERSON_ID}, "mainEntity": {"@id": PERSON_ID},
         "dateModified": site["updated"], "description": site["summary"],
         "primaryImageOfPage": {"@type": "ImageObject", "url": OG_IMAGE, "width": 1200, "height": 630}},
        {"@type": "FAQPage", "@id": f"{BASE}/#faq", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]},
        {"@type": "Blog", "@id": f"{BASE}/writing/#blog", "url": f"{BASE}/writing/", "name": f"Essays by {NAME}",
         "inLanguage": "en", "author": {"@id": PERSON_ID}, "blogPost": post_nodes},
    ]}


def crumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


# ---------------------------------------------------------------- standalone pages
CSS = """:root{color-scheme:dark;--bg:#06070a;--fg:255,255,255;--text:#eceef3;--body:#b9bfce;--muted:#8a90a2;--dim:#7b8196;--line:rgba(var(--fg),.08);--line-2:rgba(var(--fg),.14);--a1:#c6f36b;--a2:#5ee7df;--a3:#8b93ff;--a1-rgb:198,243,107;--a3-rgb:139,147,255;--on-accent:#0a0b0e;--surface:rgba(var(--fg),.028);--surface-2:rgba(var(--fg),.05);--sans:"Inter Tight",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;--serif:"Instrument Serif",Georgia,serif;--mono:ui-monospace,Consolas,monospace}
:root[data-theme="light"]{color-scheme:light;--bg:#f7f6f2;--fg:18,20,30;--text:#12141a;--body:#343a4a;--muted:#4b5162;--dim:#666c80;--a1:#4d7c0f;--a2:#0f766e;--a3:#4f46e5;--a1-rgb:77,124,15;--a3-rgb:79,70,229;--on-accent:#ffffff}
*{box-sizing:border-box;margin:0;padding:0}html{-webkit-text-size-adjust:100%}
body{background:radial-gradient(60% 40% at 85% -5%,rgba(var(--a3-rgb),.2),transparent 60%),radial-gradient(50% 40% at 0 100%,rgba(var(--a1-rgb),.08),transparent 60%),var(--bg);background-attachment:fixed;color:var(--text);font-family:var(--sans);line-height:1.6;min-height:100vh;-webkit-font-smoothing:antialiased}
a{color:inherit}:focus-visible{outline:2px solid var(--a1);outline-offset:3px;border-radius:6px}
.skip{position:absolute;left:16px;top:-80px;padding:10px 16px;border-radius:10px;background:var(--a1);color:var(--on-accent);font-weight:600;text-decoration:none}.skip:focus{top:12px}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px 16px;padding:20px 0;flex-wrap:wrap}
.logo{display:inline-flex;align-items:center;gap:10px;text-decoration:none;font-weight:600;letter-spacing:-.01em}
.mark{width:34px;height:34px;border-radius:11px;background:linear-gradient(135deg,var(--a1),var(--a3));color:var(--on-accent);display:grid;place-items:center;font-size:12.5px;font-weight:700}
.top nav{display:flex;gap:2px;flex-wrap:wrap}.top nav a{font-size:14px;color:var(--muted);text-decoration:none;padding:8px 12px;border-radius:999px;transition:.2s}.top nav a:hover{color:var(--text);background:var(--surface-2)}
main{padding:clamp(24px,5vw,56px) 0 40px}
.back{font-family:var(--mono);font-size:12px;color:var(--dim);text-decoration:none}.back:hover{color:var(--text)}
.cat{margin-top:26px;font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--a2)}
h1{font-size:clamp(32px,6vw,52px);line-height:1.05;letter-spacing:-.035em;font-weight:600;margin-top:14px}
.lede{color:var(--muted);font-size:18px;margin-top:14px;max-width:56ch}
.meta{margin-top:18px;font-family:var(--mono);font-size:12.5px;color:var(--dim);display:flex;gap:14px;flex-wrap:wrap}.meta a{color:var(--muted)}
.body{margin-top:34px;padding-top:30px;border-top:1px solid var(--line)}
.body p{color:var(--body);font-size:18px;line-height:1.75;margin:0 0 20px}
.body h2{font-size:clamp(22px,3vw,28px);letter-spacing:-.025em;font-weight:600;margin:38px 0 12px;line-height:1.15}
.pull-quote{font-family:var(--serif);font-style:italic;font-size:clamp(24px,3.2vw,32px);line-height:1.3;color:var(--text);border-left:2px solid var(--a1);padding:4px 0 4px 22px;margin:34px 0}
.cta{margin-top:44px;padding:26px;border:1px solid var(--line-2);border-radius:20px;background:var(--surface)}
.cta h2{font-size:22px;letter-spacing:-.02em;font-weight:600}.cta p{color:var(--muted);margin-top:6px}
.btn{display:inline-block;margin-top:16px;padding:12px 20px;border-radius:999px;background:var(--a1);color:var(--on-accent);font-weight:600;text-decoration:none;font-size:15px}
.more{margin-top:40px}.more h2{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);font-weight:500;margin-bottom:12px}
.more ul{list-style:none;display:grid;gap:10px}
.more a{display:block;padding:16px 18px;border:1px solid var(--line);border-radius:14px;text-decoration:none;background:var(--surface);transition:.2s}.more a:hover{border-color:var(--line-2);background:var(--surface-2)}
.more b{display:block;font-weight:600;letter-spacing:-.01em}.more span{display:block;color:var(--muted);font-size:14.5px;margin-top:3px}.more small{display:block;font-family:var(--mono);font-size:11.5px;color:var(--dim);margin-top:6px}
footer{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--dim);font-size:13px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}footer a{color:var(--muted)}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
:root[data-theme="light"] body{background:radial-gradient(60% 40% at 85% -5%,rgba(var(--a3-rgb),.1),transparent 60%),radial-gradient(50% 40% at 0 100%,rgba(var(--a1-rgb),.09),transparent 60%),var(--bg)}
:root[data-theme="light"] .more a,:root[data-theme="light"] .cta{background:#fff;box-shadow:0 1px 2px rgba(20,24,40,.04),0 16px 36px -24px rgba(20,24,40,.2)}
.theme-btn{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);display:grid;place-items:center;color:var(--muted);background:none;cursor:pointer;flex:none;transition:color .2s,border-color .2s,background .2s}
.theme-btn:hover{color:var(--text);border-color:var(--line-2);background:var(--surface-2)}
.theme-btn svg{width:17px;height:17px}
:root[data-theme="light"] .theme-btn .i-sun,:root:not([data-theme="light"]) .theme-btn .i-moon{display:none}
.top .tools{display:flex;align-items:center;gap:6px;flex-wrap:wrap}"""


def page(title, desc, path, up, og_type, body_html, ld, extra_meta=""):
    """A standalone page. `path` is the page's path ('' = home); `up` the relative prefix back to v2/."""
    url = f"{BASE}/{path}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="author" content="{esc(NAME)}">
{THEME_INIT}<meta name="color-scheme" content="dark light">
<meta name="theme-color" content="#06070a">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(NAME)} - {esc(site['jobTitle'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{OG_IMAGE}">
{extra_meta}<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{up}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
<link rel="manifest" href="{up}manifest.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="{FONT_URL}" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{FONT_URL}"></noscript>
<script type="application/ld+json">{js_json(ld)}</script>
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<header class="top">
  <a class="logo" href="{up}" aria-label="{esc(NAME)} - home"><span class="mark" aria-hidden="true">TK</span><span>{esc(NAME)}</span></a>
  <div class="tools"><nav aria-label="Primary"><a href="{up}#work">Projects</a><a href="{up}writing/">Writing</a><a href="{up}#faq">FAQ</a><a href="{up}#contact">Contact</a></nav>{THEME_BTN}</div>
</header>
<main id="main">
{body_html}
</main>
<footer><span>© {site['updated'][:4]} {esc(NAME)} · {esc(site['locality'])}, India</span><span><a href="{up}">Portfolio</a> · <a href="{site['sameAs'][0]}" rel="me noopener">LinkedIn</a> · <a href="{site['sameAs'][1]}" rel="me noopener">GitHub</a></span></footer>
</div>
{THEME_JS}
</body>
</html>
"""


def other_posts(current):
    items = "".join(
        f'<li><a href="../{p["slug"]}/"><b>{esc(p["title"])}</b><span>{esc(p["excerpt"])}</span><small>{esc(p["cat"])} · {esc(p["read"])}</small></a></li>'
        for p in posts if p["slug"] != current)
    return f'<section class="more" aria-labelledby="more-h"><h2 id="more-h">More essays</h2><ul>{items}</ul></section>'


def post_page(p):
    url = f"{BASE}/writing/{p['slug']}/"
    words = len(plain(p["body"]).split())
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "@id": f"{url}#article", "headline": p["title"], "description": clip(p["excerpt"]),
         "url": url, "mainEntityOfPage": {"@type": "WebPage", "@id": url}, "inLanguage": "en", "articleSection": p["cat"],
         "datePublished": p["iso"], "dateModified": p["iso"], "wordCount": words, "image": OG_IMAGE,
         "author": person_node(False), "publisher": person_node(False), "isPartOf": {"@id": f"{BASE}/writing/#blog"}},
        crumbs([("Home", f"{BASE}/"), ("Writing", f"{BASE}/writing/"), (p["title"], url)]),
    ]}
    body = f"""<article>
  <a class="back" href="../">← All writing</a>
  <p class="cat">{esc(p['cat'])}</p>
  <h1>{esc(p['title'])}</h1>
  <p class="meta"><span>By <a href="../../" rel="author">{esc(NAME)}</a></span><time datetime="{p['iso']}">{esc(p['date'])}</time><span>{esc(p['read'])}</span></p>
  <div class="body">
{p['body']}
  </div>
  <aside class="cta"><h2>Building something similar?</h2><p>{esc(NAME)} is open to AI engineering roles, consulting and ambitious builds in agents, RAG, voice and automation.</p><a class="btn" href="../../#contact">Get in touch</a></aside>
  {other_posts(p['slug'])}
</article>"""
    meta = f'<meta property="article:published_time" content="{p["iso"]}">\n<meta property="article:author" content="{esc(NAME)}">\n<meta property="article:section" content="{esc(p["cat"])}">\n'
    return page(f"{p['title']} - {NAME}", clip(p["excerpt"]), f"writing/{p['slug']}/", "../../", "article", body, ld, meta)


def writing_index():
    items = "".join(
        f'<li><a href="{p["slug"]}/"><b>{esc(p["title"])}</b><span>{esc(p["excerpt"])}</span><small>{esc(p["cat"])} · <time datetime="{p["iso"]}">{esc(p["date"])}</time> · {esc(p["read"])}</small></a></li>'
        for p in posts)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": f"{BASE}/writing/", "url": f"{BASE}/writing/", "name": f"Writing - {NAME}", "inLanguage": "en",
         "isPartOf": {"@id": f"{BASE}/#website"}, "about": {"@id": PERSON_ID}},
        {"@type": "Blog", "@id": f"{BASE}/writing/#blog", "url": f"{BASE}/writing/", "name": f"Essays by {NAME}", "inLanguage": "en",
         "author": person_node(False), "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": f"{BASE}/writing/{p['slug']}/", "datePublished": p["iso"]} for p in posts]},
        crumbs([("Home", f"{BASE}/"), ("Writing", f"{BASE}/writing/")]),
    ]}
    body = f"""<a class="back" href="../">← Portfolio</a>
<p class="cat">Writing</p>
<h1>Essays and writing</h1>
<p class="lede">Short essays on RAG, agents, MCP and the data engineering that keeps them honest, written from systems {esc(NAME)} has actually run.</p>
<section class="more" style="margin-top:32px" aria-label="Essays"><ul>{items}</ul></section>"""
    return page(f"Writing - {NAME}", "Essays on production AI: RAG, agents, MCP, multi-tenant backends, data quality and automation, by Tharun Kumar Reddy.", "writing/", "../", "website", body, ld)


# ---------------------------------------------------------------- index.html regions
def posts_cards():
    out = []
    for i, p in enumerate(posts):
        out.append(f'<a class="post{" lead" if i == 0 else ""}" href="writing/{p["slug"]}/" data-i="{i}"><span class="pc">{esc(p["cat"])}</span><h3>{esc(p["title"])}</h3><p>{esc(p["excerpt"])}</p><span class="pm"><span><time datetime="{p["iso"]}">{esc(p["date"])}</time> · {esc(p["read"])}</span><b>Read →</b></span></a>')
    return "".join(out)


def faq_html():
    out = []
    for i, f in enumerate(faq):
        out.append(f'<details{" open" if i == 0 else ""}><summary>{esc(f["q"])}</summary><p>{esc(f["a"])}</p></details>')
    return "\n      ".join(out)


def update_index():
    path = os.path.join(V2, "index.html")
    src = open(path, encoding="utf8", newline="").read().replace("\r\n", "\n")
    reader = [{k: p[k] for k in ("slug", "cat", "title", "date", "read", "excerpt", "body")} for p in posts]
    src = swap(src, "<!--LD:START-->", "<!--LD:END-->", f'<script type="application/ld+json">{js_json(home_graph())}</script>')
    src = swap(src, "<!--POSTS_HTML:START-->", "<!--POSTS_HTML:END-->", posts_cards())
    src = swap(src, "/*POSTS:START*/", "/*POSTS:END*/", f"const POSTS = {js_json(reader)};")
    src = swap(src, "<!--FAQ:START-->", "<!--FAQ:END-->", "\n      " + faq_html() + "\n      ")
    y, m, _ = site["updated"].split("-")
    src = swap(src, "<!--UPDATED:START-->", "<!--UPDATED:END-->", f'<time datetime="{site["updated"]}">{MONTHS[int(m) - 1]} {y}</time>')
    write("v2/index.html", src)
    return src


# ---------------------------------------------------------------- text files
def project_cards(src):
    out = []
    for block in re.findall(r'<article class="card[^>]*>(.*?)</article>', src, re.S):
        h3 = re.search(r"<h3>(.*?)</h3>", block, re.S)
        if not h3:
            continue
        p = re.search(r"<p>(.*?)</p>", block, re.S)
        desc = plain(p.group(1)) if p else "; ".join(plain(li) for li in re.findall(r"<li>(.*?)</li>", block, re.S))
        out.append((plain(h3.group(1)), desc))
    return out


def llms_short():
    pages = [f"- [Portfolio]({BASE}/): projects, platform engineering, writing, toolbox, credentials and FAQ",
             f"- [Writing]({BASE}/writing/): essays on production AI"]
    essays = [f"- [{p['title']}]({BASE}/writing/{p['slug']}/): {p['excerpt']}" for p in posts]
    return f"""# {NAME}

> {site['summary']}

## Key facts
{chr(10).join('- ' + f for f in site['facts'])}
- Location: {site['locality']}, India.
- Profiles: {', '.join(site['sameAs'])}

## Pages
{chr(10).join(pages)}

## Essays
{chr(10).join(essays)}

## Optional
- [Full text of this site for language models]({BASE}/llms-full.txt)
"""


def llms_full(src):
    out = [f"# {NAME}", "", f"> {site['summary']}", "", "## Key facts", *["- " + f for f in site["facts"]],
           f"- Location: {site['locality']}, India.", f"- Profiles: {', '.join(site['sameAs'])}", "", "## Frequently asked questions", ""]
    for f in faq:
        out += [f"### {f['q']}", f["a"], ""]
    out += ["## Projects and platform builds", ""]
    for t, d in project_cards(src):
        out += [f"### {t}", d, ""]
    out += ["## Essays", ""]
    for p in posts:
        out += [f"### {p['title']}", f"{p['cat']} · {p['date']} · {p['read']} · {BASE}/writing/{p['slug']}/", "", essay_text(p), ""]
    return "\n".join(out)


def essay_text(p):
    t = re.sub(r"</(p|h2)>", "\n\n", p["body"])
    t = re.sub(r"<h2>", "## ", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", t)).strip()


def robots():
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User",
            "Google-Extended", "Applebot-Extended"]
    lines = ["User-agent: *", "Allow: /", "",
             "# Search and AI answer engines are welcome to read and cite this site.",
             "# To opt out of a crawler, change its Allow to Disallow.", ""]
    for b in bots:
        lines += [f"User-agent: {b}", "Allow: /", ""]
    lines += [f"Sitemap: {BASE}/sitemap.xml", ""]
    return "\n".join(lines)


def sitemap():
    rows = [(f"{BASE}/", site["updated"], "1.0"), (f"{BASE}/writing/", site["updated"], "0.8")]
    rows += [(f"{BASE}/writing/{p['slug']}/", p["iso"], "0.7") for p in posts]
    body = "".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{d}</lastmod>\n    <priority>{pr}</priority>\n  </url>\n" for u, d, pr in rows)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n'


# ---------------------------------------------------------------- run
src = update_index()
write("v2/llms.txt", llms_short())
write("v2/llms-full.txt", llms_full(src))
write("v2/robots.txt", robots())
write("v2/sitemap.xml", sitemap())
write("v2/writing/index.html", writing_index())
for p in posts:
    write(f"v2/writing/{p['slug']}/index.html", post_page(p))

# remove essay folders that no longer exist in posts.json
wdir = os.path.join(V2, "writing")
if os.path.isdir(wdir):
    keep = {p["slug"] for p in posts}
    for d in os.listdir(wdir):
        full = os.path.join(wdir, d)
        if os.path.isdir(full) and d not in keep:
            stale.append(f"v2/writing/{d}/ (removed)")
            if not CHECK:
                shutil.rmtree(full)

if CHECK:
    if stale:
        print("Out of date (run: python scripts/build.py):")
        for s in stale:
            print("  ", s)
        sys.exit(1)
    print("Generated files are up to date.")
else:
    print(f"Built {len(posts)} essay pages, FAQ ({len(faq)}), sitemap, robots, llms files.")
    for s in stale:
        print("  wrote", s)
