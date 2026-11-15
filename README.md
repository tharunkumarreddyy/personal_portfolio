# Tharun Kumar Reddy — Portfolio

A fast, dependency-free static portfolio. Plain HTML, CSS and JavaScript: no build step, no framework, no tracking.

**The live site is the `v2/` folder.** It is deployed to GitHub Pages by `.github/workflows/deploy-pages.yml`.

```
v2/
  index.html        the whole site (projects, platform work, writing, toolbox, credentials)
  404.html          not-found page
  robots.txt        crawler rules  (URL filled in at deploy time)
  sitemap.xml       sitemap        (URL filled in at deploy time)
  assets/
    profile.webp    portrait used on the page
    og-image.png    1200×630 link-preview image
    Tharun_Kumar_Reddy_Resume.pdf   résumé download
scripts/
  check_site.py     pre-deploy checks (broken links, JSON-LD, private-name guard)
.github/workflows/
  deploy-pages.yml  builds and publishes v2/ to GitHub Pages
```

`resume/resume.html` is the editable source of the résumé PDF (see "Updating the site").

## Run it locally

```bash
python -m http.server 5178 --directory v2
```

Then open <http://localhost:5178>. The `__SITE_URL__` tokens in the meta tags are only filled in during deploy, which does not affect how the page looks.

## Check before you push

```bash
python scripts/check_site.py v2
```

Fails on missing local files or invalid structured data. If `scripts/banned-terms.local.txt` exists (it is git-ignored), it also fails when any listed private name appears in the site.

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

- **Content and layout:** edit `v2/index.html`. Project cards live under `<!-- WORK -->` and `<!-- PLATFORMS -->`. Blog posts are the `POSTS` array in the script at the bottom of the file.
- **Résumé:** edit `resume/resume.html`, then regenerate the PDF with Microsoft Edge (or Chrome) from the repo root. On Windows PowerShell:

  ```powershell
  & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --no-pdf-header-footer `
    "--print-to-pdf=$PWD\v2\assets\Tharun_Kumar_Reddy_Resume.pdf" "file:///$($PWD -replace '\\','/')/resume/resume.html"
  ```

  Or simply replace `v2/assets/Tharun_Kumar_Reddy_Resume.pdf` with your own file, keeping the filename.
- **Link-preview image:** replace `v2/assets/og-image.png` (1200×630).
- Push to `main` and the workflow redeploys.

## Privacy notes

- The page contains your email address, LinkedIn link and city, but no phone number.
- Keep private client or product names out of the page. List them in `scripts/banned-terms.local.txt` so the check catches slips.
- If the repository is public, everything in it is public, including its git history.
