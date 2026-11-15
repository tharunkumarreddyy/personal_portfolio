#!/usr/bin/env python3
"""Pre-deploy sanity check for the static site. Standard library only.

Usage:  python scripts/check_site.py v2

Checks
  1. every local href/src in the HTML files points to a file that exists
  2. JSON-LD blocks parse
  3. no unresolved __SITE_URL__ token (only enforced in CI, where the workflow fills it in)
  4. optional: terms listed in scripts/banned-terms.local.txt (one per line, git-ignored)
     must not appear in any published text file. Use it to keep private project or
     client names out of the site.

Exit code 1 if anything fails.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "v2")
in_ci = os.environ.get("CI") == "true"
errors, warnings = [], []


class Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.jsonld, self._ld = [], [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])
        if tag == "script" and a.get("type") == "application/ld+json":
            self._ld = True
            self.jsonld.append("")

    def handle_endtag(self, tag):
        if tag == "script":
            self._ld = False

    def handle_data(self, data):
        if self._ld:
            self.jsonld[-1] += data


html_files = []
text_files = []
for dp, _, fs in os.walk(root):
    for f in fs:
        p = os.path.join(dp, f)
        if f.endswith(".html"):
            html_files.append(p)
        if f.endswith((".html", ".xml", ".txt", ".css", ".js", ".json", ".svg")):
            text_files.append(p)

for path in html_files:
    rel = os.path.relpath(path, root)
    src = open(path, encoding="utf8").read()
    parser = Refs()
    parser.feed(src)
    for ref in parser.refs:
        if re.match(r"^(https?:|mailto:|tel:|data:|#|javascript:|//)", ref) or "__SITE_URL__" in ref:
            continue
        target = os.path.join(os.path.dirname(path), ref.split("#")[0].split("?")[0])
        if not os.path.exists(target):
            errors.append(f"{rel}: missing local file -> {ref}")
    for block in parser.jsonld:
        try:
            json.loads(block)
        except ValueError as e:
            errors.append(f"{rel}: invalid JSON-LD ({e})")

for path in text_files:
    rel = os.path.relpath(path, root)
    src = open(path, encoding="utf8", errors="ignore").read()
    if "__SITE_URL__" in src:
        (errors if in_ci else warnings).append(f"{rel}: still contains __SITE_URL__ (the deploy workflow fills it in)")

banned_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banned-terms.local.txt")
if os.path.exists(banned_file):
    terms = [t.strip().lower() for t in open(banned_file, encoding="utf8") if t.strip() and not t.startswith("#")]
    for path in text_files:
        low = open(path, encoding="utf8", errors="ignore").read().lower()
        for t in terms:
            if t in low:
                errors.append(f"{os.path.relpath(path, root)}: contains banned term '{t}'")
else:
    warnings.append("no scripts/banned-terms.local.txt, skipping private-name check")

print(f"Checked {len(html_files)} HTML file(s) in {root}")
for w in warnings:
    print("  warn :", w)
for e in errors:
    print("  ERROR:", e)
if errors:
    sys.exit(1)
print("OK")
