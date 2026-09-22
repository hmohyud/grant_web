# grant_web

Redesign work for [nonprofitmegaphone.com](https://nonprofitmegaphone.com/), the Google Ad Grant management agency.

Live: **https://hmohyud.github.io/grant_web/**

## What is here

| Path | What it is |
|---|---|
| `site/` | Everything that gets deployed to GitHub Pages. |
| `site/index.html` | Style explorer: toggle through the design directions at desktop and phone width. |
| `site/pitch/` | The full pitch page: research brief, five finalist directions with live mockups, panel scores, recommendation. |
| `site/directions/` | The hero mockups, one desktop and one phone file per direction, plus each direction's spec as JSON. |
| `site/directions/first-round/` | The three directions cut after the first judging round, desktop hero only. |
| `reference/` | A saved export of the current live site, kept for reference. Not deployed. |
| `tools/` | `build_pitch.py` and `pitch_data.json`, which generate the pitch page. |
| `.github/workflows/deploy.yml` | Deploys `site/` to GitHub Pages on every push to `main`. |

## Directions

1. **Amplitude** (recommended): warm paper, vermilion signal arcs grown from the megaphone mark, Bricolage Grotesque + Hanken Grotesk.
2. **Broadsheet** (runner-up): newsprint white, the brand's deep blue as the only color, Newsreader + Schibsted Grotesk.
3. **Public Works**: white, civic-blue blocks, signal-red CTA, Public Sans, a grant account record as the hero object.
4. **Full Volume**: keeps the electric blue as a bordered stage with stickers and a highlighter; the evolutionary option.
5. **Signed Sentence**: linen, forest green and ochre, Fraunces, a signed monthly note beside documentary photography.
6. **Placard** (added later): mid-century civic poster fields of mustard and teal, Archivo Black, a geometric megaphone.
7. **Itemized** (added later): the monthly receipt for $10,000 of donated ads as the hero object, ink green stamp, JetBrains Mono.
8. **Atlas** (added later): reach drawn as a contour map on pale steel blue, Source Serif 4, coral pins.
9. **Open Air** (added later): a calm pale-sky ground, light Manrope type, proof as floating chips.
10. **Rings** (added later): every shape a circle; a ring meter as the hero on a soft lilac ground, Outfit + Figtree, one violet.
11. **Top Result** (added later): Google's own idiom, white and Roboto, the four colors only as hairlines, a search-results mock as the hero.

Directions 6 to 11 were added as alternatives after the first judging round and have not been scored by the panel. `tools/build_pitch.py` rebuilds `site/pitch/index.html` from the direction files and `tools/pitch_data.json`.

## Deploying

Push to `main`. The workflow uploads `site/` and publishes it. Pages must be set to deploy from **GitHub Actions** (Settings → Pages → Source); the workflow tries to enable this itself on the first run.

Everything is static HTML and CSS with Google Fonts, so there is no build step. Open `site/index.html` locally or serve the folder with any static server:

```bash
python -m http.server 8000 --directory site
```
