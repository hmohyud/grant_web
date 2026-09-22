# grant_web

Redesign work for [nonprofitmegaphone.com](https://nonprofitmegaphone.com/), the Google Ad Grant management agency.

Live: **https://hmohyud.github.io/grant_web/**

## What is here

| Path | What it is |
|---|---|
| `site/` | Everything that gets deployed to GitHub Pages. |
| `site/index.html` | Style explorer: toggle through the design directions at desktop and phone width. |
| `site/pitch/` | The full pitch page: research brief, five finalist directions with live mockups, panel scores, recommendation. |
| `site/directions/` | The finalist hero mockups, one desktop and one phone file per direction, plus each direction's spec as JSON. |
| `site/directions/first-round/` | The three directions cut after the first judging round, desktop hero only. |
| `reference/` | A saved export of the current live site, kept for reference. Not deployed. |
| `.github/workflows/deploy.yml` | Deploys `site/` to GitHub Pages on every push to `main`. |

## Directions

1. **Amplitude** (recommended): warm paper, vermilion signal arcs grown from the megaphone mark, Bricolage Grotesque + Hanken Grotesk.
2. **Broadsheet** (runner-up): newsprint white, the brand's deep blue as the only color, Newsreader + Schibsted Grotesk.
3. **Public Works**: white, civic-blue blocks, signal-red CTA, Public Sans, a grant account record as the hero object.
4. **Full Volume**: keeps the electric blue as a bordered stage with stickers and a highlighter; the evolutionary option.
5. **Signed Sentence**: linen, forest green and ochre, Fraunces, a signed monthly note beside documentary photography.

## Deploying

Push to `main`. The workflow uploads `site/` and publishes it. Pages must be set to deploy from **GitHub Actions** (Settings → Pages → Source); the workflow tries to enable this itself on the first run.

Everything is static HTML and CSS with Google Fonts, so there is no build step. Open `site/index.html` locally or serve the folder with any static server:

```bash
python -m http.server 8000 --directory site
```
