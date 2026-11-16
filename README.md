# Tharun Kumar Reddy — Portfolio

A fast static portfolio. Plain HTML, CSS and JavaScript with no framework and no tracking. A small standard-library Python script generates the search-engine pages (essays, FAQ, structured data, sitemap).

**The live site is the `v2/` folder.** It is deployed to GitHub Pages by `.github/workflows/deploy-pages.yml`.

```
content/            the text that generates the SEO pages (edit these)
  site.json         name, role, links, key facts, "updated" date
  posts.json        the essays
  faq.json          the FAQ (shown on the page and published as FAQPage data)
v2/
  index.html        the single-page site (projects, platform work, writing, toolbox, credentials, FAQ)
  writing/          GENERATED: one page per essay, plus an index
  404.html          not-found page
  llms.txt, llms-full.txt   GENERATED: plain-text summaries for AI tools
  robots.txt, sitemap.xml   GENERATED (URL filled in at deploy time)
  favicon.*, apple-touch-icon.png, manifest.webmanifest   icons
  assets/
    profile.webp    portrait used on the page
    og-image.png    1200×630 link-preview image
    Tharun_Kumar_Reddy_Resume.pdf   résumé download
resume/resume.html  editable source of the résumé PDF
scripts/
  build.py          generates the pages listed above from content/
  check_site.py     pre-deploy checks (links, titles, canonicals, JSON-LD, sitemap, private-name guard)
.github/workflows/
  deploy-pages.yml  checks and publishes v2/ to GitHub Pages
```

`resume/resume.html` is the editable source of the résumé PDF (see "Updating the site").

## Run it locally

```bash
python -m http.server 5178 --directory v2
```

Then open <http://localhost:5178>. The `__SITE_URL__` tokens in the meta tags are only filled in during deploy, which does not affect how the page looks.

## Check before you push

```bash
python scripts/build.py          # regenerate essays, FAQ, sitemap, llms.txt from content/
python scripts/check_site.py v2  # verify the result
```

`build.py --check` is also run by the deploy workflow and fails if the generated files are out of date, so always run `build.py` and commit its output after editing anything in `content/`.

`check_site.py` fails on missing local files, missing titles, descriptions or canonical links, pages without exactly one `<h1>`, invalid structured data, or a sitemap entry with no page. If `scripts/banned-terms.local.txt` exists (it is git-ignored), it also fails when any listed private name appears in the site.

**Manual check — the résumé PDF.** The checker cannot read inside PDFs. After regenerating it, open `v2/assets/Tharun_Kumar_Reddy_Resume.pdf` and confirm it contains only what you are happy to publish. The current one lists your email, LinkedIn and city, but no phone number or private project names.

## Deploy to GitHub Pages

1. Create an empty repository on GitHub (for example `portfolio`), then push this folder to it:

   ```bash
   git init -b main
   git add .
   git commit -m "Initial portfolio"
   git remote add origin https://github.com/<your-username>/portfolio.git
   git push -u origin main
   ```

2. In the repository go to **Settings → Pages** and set **Source** to **GitHub Actions**.
3. The workflow runs on every push to `main` that touches `v2/`. When it finishes, the site is at `https://<your-username>.github.io/portfolio/`. Progress is under the **Actions** tab, and you can re-run it from there with **Run workflow**.

### Using your own domain

1. Add a repository variable **`SITE_URL`** (Settings → Secrets and variables → Actions → Variables), for example `https://tharunreddy.dev`. The workflow uses it for the canonical link, Open Graph tags, sitemap and robots.txt.
2. In **Settings → Pages → Custom domain**, enter the domain and add the DNS records GitHub shows you.

Without `SITE_URL` the workflow defaults to `https://<owner>.github.io/<repo>`.

## Updating the site

- **Layout and projects:** edit `v2/index.html`. Project cards live under `<!-- WORK -->` and `<!-- PLATFORMS -->`. Do not edit the regions between `<!--NAME:START-->` and `<!--NAME:END-->` markers by hand (structured data, essay cards, FAQ, updated date); `build.py` regenerates them.
- **Essays:** add or edit entries in `content/posts.json` (`slug`, `cat`, `title`, `date`, `iso`, `read`, `excerpt`, `body` as HTML), then run `python scripts/build.py`. Each essay gets its own page, a sitemap entry and a card on the home page.
- **FAQ:** edit `content/faq.json`. Keep each answer to 40 to 70 words, written to stand alone, because answer engines quote them.
- **Light and dark themes:** the site follows the visitor's system setting, and the sun/moon button in the top bar overrides it (saved in the browser). Every colour is a token defined once in `:root` (dark) and `:root[data-theme="light"]` (light) at the top of the `<style>` block in `v2/index.html`, and again in the `CSS` string in `scripts/build.py` for the essay pages. Change a colour there instead of hard-coding one; use `rgba(var(--fg),.08)`-style tints for overlays so both themes work. The `svg [fill="#…"]` rules map the diagrams' built-in colours onto the tokens.
- **Facts and dates:** edit `content/site.json` and bump `updated` whenever you change something meaningful.
- **Assistant ("Ask about Tharun"):** a chat widget that answers from the page's own content. It runs entirely in the browser: no server, no API key, nothing sent anywhere. Its answers live in the `KB` array in the script at the bottom of `v2/index.html` (search for `portfolio assistant`). Each entry has `k` (keywords and phrases to match), `a` (the answer, as HTML), `act` (buttons), and `next` (follow-up suggestions). When you add a project or change a number on the page, update the matching entry so the assistant stays in sync.
- **Résumé:** edit `resume/resume.html`, then regenerate the PDF with Microsoft Edge (or Chrome) from the repo root. On Windows PowerShell:

  ```powershell
  & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --no-pdf-header-footer `
    "--print-to-pdf=$PWD\v2\assets\Tharun_Kumar_Reddy_Resume.pdf" "file:///$($PWD -replace '\\','/')/resume/resume.html"
  ```

  Or simply replace `v2/assets/Tharun_Kumar_Reddy_Resume.pdf` with your own file, keeping the filename.
- **Link-preview image:** replace `v2/assets/og-image.png` (1200×630).
- Push to `main` and the workflow redeploys.

## After the first deploy (search visibility)

1. **Google Search Console:** add the site as a property, verify it, and submit `sitemap.xml`. Do the same in **Bing Webmaster Tools**.
2. **Custom domain:** see above; it is the strongest single trust signal, and the workflow updates every canonical link automatically.
3. **Test:** run the home page and an essay through Google's Rich Results Test and PageSpeed Insights.
4. **AI crawlers:** `robots.txt` currently allows the main AI search and answer crawlers (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended and others). To opt one out, change its `Allow` to `Disallow` in `scripts/build.py` and rebuild.

## Privacy notes

- The page contains your email address, LinkedIn link and city, but no phone number.
- Keep private client or product names out of the page. List them in `scripts/banned-terms.local.txt` so the check catches slips.
- If the repository is public, everything in it is public, including its git history.
