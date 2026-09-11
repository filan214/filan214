# Run your profile locally on Windows

The repository is the `filan214` folder. All eight SVGs are committed, so GitHub can display them immediately after you push. The original JPEG remains outside the repository; its local copy under `assets/` is ignored. `prep_photo.py` has deliberately not been run: use it only once you provide the source photo you want processed.

## 1. Open PowerShell in this repository

```powershell
cd 'D:\TUGAS\C Path\Portfolio\Github Profile\filan214'
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r scripts/requirements.txt
```

Python 3.11+ works for the daily scripts; GitHub Actions uses 3.11. If only Python 3.13 is installed, use `py -3.13 -m venv .venv` for the daily scripts and the existing JPEG. The optional rembg pipeline may need Python 3.11 depending on available ONNX/OpenCV wheels. A local `.venv` created during setup can be activated directly without recreating it.

If PowerShell blocks activation, either allow it for this shell only with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, or invoke `.\.venv\Scripts\python.exe` in place of `python` throughout. No global execution-policy change is needed.

## 2. Confirm your manual thesis status

`data/status.json` already contains your requested starting example:

```json
{
  "objectives_done": 5,
  "objectives_total": 5,
  "defense_status": "pending"
}
```

Edit it in your editor. The numbers must be integers, total must be positive, and done cannot exceed total. Defense is separate text: 5/5 objectives does not mean the defense has happened. The values are hand-maintained and never scraped.

```powershell
python scripts/render_status_bar.py
```

This updates `thesis-progress.svg`. The workflow repeats it after every push to `main`, including a manual edit made through GitHub. The htop panel is illustrative: its 89% is mock activity, not this completion ratio. Edit `PROCESSES` in `scripts/make_status_panel.py` to change those labels.

## 3. Generate the portrait from your existing reference

Only Pillow is needed for an existing JPEG:

```powershell
python -m pip install pillow
python scripts/make_ascii_svg.py '..\filan-ascii.jpg'
```

You can also use the ignored local copy:

```powershell
python scripts/make_ascii_svg.py assets/filan-ascii.jpg
```

The 100 × 53 character grid preserves the photo's aspect ratio with whitespace padding and uses the requested ramp. This direct conversion keeps the reference image's background. Source photos are never embedded in the resulting SVG.

Later, after supplying a source photo, optionally run the full preparation pipeline:

```powershell
python -m pip install -r scripts/requirements-portrait.txt
python scripts/prep_photo.py 'C:\path\to\your-source-photo.jpg'
python scripts/make_ascii_svg.py
```

The pipeline removes the background with rembg, boosts luminance contrast using CLAHE, composites onto white, and saves `assets/portrait-gray.png`. rembg downloads its model on first use. The CPU extra provides the ONNX runtime. Portrait dependencies and model downloads are excluded from daily CI.

## 4. Build the other static panels

```powershell
python scripts/make_info_card.py
python scripts/make_status_panel.py
python scripts/make_tagline.py
```

These emit `info-card.svg`, `status-panel.svg`, and `tagline.svg`. Edit the copy directly in their scripts and rerun when your biography changes.

## 5. Fetch and render live GitHub data

```powershell
python scripts/fetch_contributions.py
python scripts/render_heatmap_svg.py
python scripts/fetch_last_event.py
python scripts/render_commit_log.py
python scripts/fetch_languages.py
python scripts/render_languages_svg.py
```

Each fetcher updates its corresponding `data/*.json`, and each renderer reads that file. A failure exits with an error and preserves the existing snapshot. The scripts use public requests without tokens or `.netrc` credentials. Unauthenticated API limits are shared by IP; if limited, wait until the reset reported by the script instead of repeatedly retrying.

- Contributions: exact counts are parsed from GitHub's tooltips or legacy count attributes. The fetcher combines each calendar year intersecting the 53-week window because the endpoint selects a single year when given an end date. Streaks are bounded by that window. A present, zero-contribution today can continue yesterday's streak; missing dates break it. Monthly totals are stored in JSON. The calendar uses 53 Sunday-first weeks, with dashed cells for unavailable/future dates; the brightest of six green levels marks peak days. Dates are evaluated in Asia/Jakarta (UTC+07).
- Latest event: public events are a limited, potentially delayed history. When PushEvent omits its message, the script fetches the event's exact head commit. No public push produces an explicit empty state. Deleted/inaccessible commits fail without silently substituting another commit.
- Languages: every page of owned public repos is read, including forks if any. Real byte counts come from each repo's language endpoint. Top six bars are shares of the full byte total, so hidden languages can make visible percentages sum below 100%. These are code proportions, not skill ratings. Unchanged repo results are cached by `pushed_at`; Sunday runs refresh everything to pick up delayed language processing. All repo snapshots stay inside `data/languages.json`, so the requested workflow file pattern captures the cache.

## 6. Inspect and verify

```powershell
python -m unittest discover -s tests -v
python scripts/make_preview.py
python -m http.server 8000 --bind 127.0.0.1
```

Open [the local preview](http://localhost:8000/preview/) in your browser. The server is only for local inspection; there is nothing to deploy. Use browser developer tools to emulate light/dark `prefers-color-scheme` and reduced motion. GitHub can shrink images to its available content width and applies its own table cell padding. SVG intrinsic widths are 860, with a 370/490 portrait/card pair. The browser/OS color preference drives media queries inside external SVGs; a manually selected GitHub theme may differ from that preference.

All SVGs have embedded light/dark CSS, title/description, and no script or external stylesheet. Every README image has alt text. The portrait, calendar, panels, commit line, and bars animate once; only the tagline loops. Reduced motion shows the final content and all four tagline phrases.

For a static info-card preview:

```powershell
$env:STATIC = '1'
python scripts/make_info_card.py
Remove-Item Env:STATIC
```

That command replaces `info-card.svg` with its frozen frame. Run `python scripts/make_info_card.py` again after removing the environment variable to restore animation. `STATIC=1` is supported by every SVG generator. `make_preview.py --static` writes frozen copies under ignored `preview/static/` without replacing committed SVGs.

## 7. Review the local commit and publish yourself

```powershell
git status
git log -1 --format=fuller
git remote -v
```

The local repository uses `Valentinus Filan <valentinus.filan@gmail.com>` as author and committer, with no co-author trailer. Verify that email belongs to your GitHub account: attribution comes from commit metadata, not who presses Push. The workflow also uses this identity; GitHub Actions still performs the automated push when you enable it.

Create an **empty public** repository named **filan214** under your GitHub account (do not initialize a README, license, or .gitignore). The local origin is prepared as `https://github.com/filan214/filan214.git`. Then, when you are ready:

```powershell
git push -u origin main
```

This is your step; it has not been run for you. If you make local edits after the initial commit, first stage the intended files and commit them yourself.

The first push containing `.github/workflows/update-profile-art.yml` starts the workflow if Actions are enabled. It subsequently runs daily at 07:17 Jakarta, on pushes to `main`, and from **Actions → Update profile art → Run workflow**. It installs only requests/BeautifulSoup, runs data/renderer tests, refreshes the three feeds, and renders your manual thesis bar. `contents: write` lets the auto-commit action save the generated files. The commit message includes `[skip ci]` to avoid a refresh loop. Branch protection may require allowing these updates. GitHub can delay scheduled runs or disable schedules in inactive public repositories.

To review the published README before any workflow runs, disable Actions for the new repository before your initial push, inspect the profile, then enable Actions and run the workflow manually. No workflow or remote repository was enabled by the local build.

Reference: [GitHub profile README setup](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme), [event payloads](https://docs.github.com/en/rest/using-the-rest-api/github-event-types), [repository languages](https://docs.github.com/en/rest/repos/repos#list-repository-languages), [API rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), and [auto-commit action inputs](https://github.com/stefanzweifel/git-auto-commit-action/tree/v5).
