# GitHub profile art implementation plan

**Goal:** Build the requested filan214 profile repository, verify it locally, and commit as Valentinus Filan without pushing.

**Architecture:** Small Python fetchers write JSON snapshots; independent renderers emit self-contained SVGs. A shared helper provides accessible markup, light/dark colors, terminal chrome, safe XML text, and static/reduced-motion handling. No service, token, external stylesheet, or JavaScript is needed.

**Stack:** Python 3.11+, requests 2.32.3, BeautifulSoup 4.12.3; Pillow for the existing portrait; optional NumPy/OpenCV/rembg for a future source photo.

**Specification:** User's detailed script, SVG, README ordering, width, Windows setup, workflow, and sole-author/local-commit requirements in this task.

## Decisions

- Repository root is `filan214/`. Preserve the original JPEG outside the repository; copy a reference into ignored `assets/` for local generation.
- `scripts/requirements.txt` contains only the two cron dependencies. `scripts/requirements-portrait.txt` contains the optional portrait tools and ONNX CPU runtime needed by rembg.
- Use light colors by default and a dark media override inside every SVG. `STATIC=1` removes animations for all generators; reduced motion displays the completed frame.
- GitHub's current PushEvent provides `head`; request that exact commit when the event omits messages. Never substitute a different commit.
- Paginate public owned repositories and events. Sum real language bytes, including forks if present. Cache language responses by repository push timestamp to reduce unauthenticated request volume.
- Fail clearly on unavailable/malformed upstream data and retain the last valid JSON. Never represent an API failure as zero activity.
- Calendar has exactly 53 Sunday-first weeks. Future or unavailable cells are visibly distinct from zero-contribution days. Streaks cover the returned calendar window, allow today to be unfinished, and stop at missing dates.
- Status starts with the user's example: 5 of 5 objectives, defense pending. The htop percentages are explicitly mock process activity, independent of objective completion.
- Workflow uses the configured user's name/email for both author and committer. No co-author trailers. The workflow is committed but cannot run remotely until the user creates and pushes the repository.

## Implementation checklist

- [x] Write/run regression tests for contribution parsing, streak gaps, pagination, exact commit lookup, language byte totals, and status validation.
- [x] Implement fetchers, JSON helpers, and shared SVG theme/animation primitives.
- [x] Implement every requested renderer and optional photo preparation script.
- [x] Add initial manual status, ordered README, daily workflow, Windows walkthrough, and ignored preview generator.
- [x] Fetch live data, generate all eight SVGs from the existing JPEG and JSON, run automated checks, and inspect light/dark animated/static browser output.
- [x] Request an independent code review, resolve material findings, and rerun relevant checks.

Final handoff: initialize `main`, configure the existing user identity locally, add the expected origin, commit reviewed project files only, and verify author/committer and clean status. Never push.

## Verification record

- 23 unit/renderer tests pass on local Python 3.13.2. All 15 scripts also parse using Python 3.11 grammar; the remote Python 3.11 workflow has not run.
- Live calendar: 371 dates, September 7, 2025 through September 12, 2026. Requests for each intersecting year are combined because GitHub ignores cross-year `from` ranges on this endpoint.
- Live language snapshot: 2,958,290 bytes across 15 public repositories. The last-event snapshot resolves the exact head SHA of the latest available public PushEvent.
- All eight SVGs load as external images in Edge. Sixteen individual light/dark checks pass with no out-of-bounds text; SMIL freezes at complete clip widths. Reduced-motion portrait and tagline behavior passes. Static copies and all four looping tagline states were generated for inspection.
- README image targets, alt attributes, section headers, and SVG widths are verified. Workflow YAML parses and has the requested triggers, permissions, dependency pins, refresh steps, commit message, file pattern, and user identity.
- Independent review found a missing-today streak edge case. It was reproduced with a failing test, fixed, and verified.
- Original photo preparation and remote publishing remain user-controlled steps documented in `LOCAL_SETUP.md`.
