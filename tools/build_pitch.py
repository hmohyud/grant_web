"""Build site/pitch/index.html from site/directions/ and tools/pitch_data.json.

  python tools/build_pitch.py            # site build: mockups load from ../directions/ (small page)
  python tools/build_pitch.py --embed    # standalone build: mockups embedded via srcdoc (for the claude.ai artifact)
"""
import json, re, html, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = os.path.join(ROOT, 'site', 'directions')
OUT = os.path.join(ROOT, 'site', 'pitch', 'index.html')
EMBED = '--embed' in sys.argv

def rd(p): return open(p, encoding='utf-8').read()
def js(p): return json.loads(rd(p))
def esc(s): return html.escape(str(s if s is not None else ''), quote=True)
def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

DATA = js(os.path.join(ROOT, 'tools', 'pitch_data.json'))
NUMBER_WORDS = {3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve'}

# ---------- load directions ----------
finals = []
for f in DATA['order']:
    p = os.path.join(DIRS, f + '.json')
    if not os.path.exists(p):
        print('skip (missing):', f); continue
    d = js(p); d['file'] = f
    d['desktop'] = f'../directions/{f}.html'; d['mobile'] = f'../directions/{f}-mobile.html'
    d['desktopHtml'] = rd(os.path.join(DIRS, f + '.html')); d['mobileHtml'] = rd(os.path.join(DIRS, f + '-mobile.html'))
    c = DATA['compact'].get(f, {})
    d['oneLiner'] = c.get('oneLiner') or d.get('oneLiner', '')
    d['bullets'] = c.get('bullets') or d.get('bullets') or [d.get('distinctFrom', '')]
    d['rightForShort'] = c.get('rightFor') or d.get('rightFor') or ''
    d['needs'] = c.get('needs') or d.get('needs') or []
    d['matrix'] = {k: c.get(k, '') for k in ('ground', 'accent', 'type', 'device', 'register')}
    d['isNew'] = f in DATA.get('new', [])
    d['badge'] = DATA['badges'].get(f, '')
    finals.append(d)

cuts = []
for f, info in DATA['firstRound'].items():
    p = os.path.join(DIRS, 'first-round', f + '.json')
    if not os.path.exists(p): continue
    d = js(p); d['file'] = f; d['angle'] = info['angle']; d['why'] = info['why']
    d['desktop'] = f'../directions/first-round/{f}.html'; d['desktopHtml'] = rd(os.path.join(DIRS, 'first-round', f + '.html'))
    cuts.append(d)

# ---------- helpers ----------
FONT_ALIASES = {'satoshi': 'Instrument Sans', 'general sans': 'Manrope', 'clash display': 'Bricolage Grotesque', 'switzer': 'Inter', 'sentient': 'Instrument Serif'}
FS_TO_GF = {'switzer': 'Inter', 'clash-display': 'Bricolage Grotesque', 'satoshi': 'Instrument Sans', 'general-sans': 'Manrope', 'sentient': 'Instrument Serif'}

def fix_fonts(h):
    """Only needed for --embed: the artifact viewer blocks Fontshare, so swap for Google equivalents."""
    swaps = []
    def repl(m):
        fams = re.findall(r'f\[\]=([a-z0-9\-]+)', m.group(0)); gf = []
        for f in fams:
            g = FS_TO_GF.get(f, 'Manrope'); swaps.append((' '.join(w.capitalize() for w in f.split('-')), g))
            gf.append('family=' + g.replace(' ', '+') + ':ital,wght@0,400;0,500;0,600;0,700;0,800;1,400')
        return 'https://fonts.googleapis.com/css2?' + '&'.join(gf) + '&display=swap'
    h2 = re.sub(r"https?://api\.fontshare\.com/[^\s\"')]+", repl, h)
    for old, new in set(swaps): h2 = h2.replace(old, new)
    return h2

def font_name(spec):
    if not spec: return ''
    m = re.match(r'\s*([A-Za-z][A-Za-z0-9 ]*?)\s*(?:[\(,\-–—/;:]|\d|\bvariable\b|$)', spec)
    name = (m.group(1) if m else spec).strip()
    return FONT_ALIASES.get(name.lower(), name)

def md_inline(s):
    s = esc(s); s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s); return s

def md_block(s):
    if isinstance(s, list): s = '\n'.join('- ' + str(x) for x in s)
    out, buf, lst = [], [], []
    def fp():
        if buf: out.append('<p>' + md_inline(' '.join(buf)) + '</p>'); buf.clear()
    def fl():
        if lst: out.append('<ul>' + ''.join('<li>' + md_inline(x) + '</li>' for x in lst) + '</ul>'); lst.clear()
    for line in str(s).split('\n'):
        t = line.strip()
        if not t: fp(); fl(); continue
        m = re.match(r'^(?:[-*•]|\d+[.)])\s+(.*)', t)
        if m: fp(); lst.append(m.group(1)); continue
        fl(); buf.append(t)
    fp(); fl(); return '\n'.join(out)

def role_hex(pal, pat, default):
    for p in pal:
        if re.search(pat, p.get('role', ''), re.I): return p['hex']
    return default

def strip(pal, n=8, hexes=True):
    cells = ''.join(f'<span class="sw" title="{esc(p.get("role",""))}"><i style="background:{esc(p.get("hex"))}"></i>' + (f'<code>{esc(p.get("hex"))}</code>' if hexes else '') + '</span>' for p in pal[:n])
    return f'<div class="strip">{cells}</div>'

def mini(pal, n=6):
    return '<span class="mini" aria-hidden="true">' + ''.join(f'<i style="background:{esc(p.get("hex","#000"))}"></i>' for p in pal[:n]) + '</span>'

def frame(title, d, kind, idx, lazy=True):
    w, h = (1200, 860) if kind == 'desktop' else (390, 800)
    if EMBED:
        src_attr = f'srcdoc="{esc(fix_fonts(d["desktopHtml"] if kind == "desktop" else d["mobileHtml"]))}"'
    else:
        src_attr = f'src="{esc(d["desktop"] if kind == "desktop" else d["mobile"])}"'
    return f'''<figure class="frame {kind}">
  <div class="chrome"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="url">nonprofitmegaphone.com</span><span class="tag">{esc(title)}</span></div>
  <div class="viewport" style="--w:{w};--h:{h}"><iframe title="{esc(title)}" {src_attr}{' loading="lazy"' if lazy else ''} sandbox="allow-same-origin" tabindex="-1"></iframe></div>
</figure>'''

def details(d):
    typ = d.get('typography', {}); hc = d.get('heroCopy', {})
    parts = [
        ('The idea', md_block(d.get('concept', ''))),
        ('Hero copy', f'<p><em>{esc(hc.get("eyebrow",""))}</em></p><p><strong>{esc(hc.get("headline",""))}</strong></p><p>{esc(hc.get("sub",""))}</p><p>Button: {esc(hc.get("cta",""))}</p>'),
        ('Type', f'<p><strong>Display:</strong> {esc(typ.get("display",""))}</p><p><strong>Body:</strong> {esc(typ.get("body",""))}</p>' + (f'<p><strong>Mono:</strong> {esc(typ.get("mono"))}</p>' if typ.get('mono') else '') + f'<p>{esc(typ.get("scaleNotes",""))}</p>'),
        ('Homepage, top to bottom', md_block(d.get('layout', ''))),
        ('Imagery', md_block(d.get('imagery', ''))), ('Motion', md_block(d.get('motion', ''))),
        ('On a phone', md_block(d.get('mobile', ''))), ('Accessibility', md_block(d.get('a11y', ''))),
        ('Signature moments', md_block(d.get('signatureMoments', []))), ('Dependencies', md_block(d.get('dependencies', []))),
        ('Risks', md_block(d.get('risks', []))), ('References', md_block(', '.join(d.get('references', [])))),
    ]
    return '<details class="more"><summary>Full spec</summary><div class="more-grid">' + ''.join(f'<section><h4>{esc(t)}</h4>{b}</section>' for t, b in parts) + '</div></details>'

def chapter(d, idx):
    pal = d.get('palette', []); typ = d.get('typography', {})
    disp = font_name(typ.get('display', '')); body = font_name(typ.get('body', ''))
    badge = f'<span class="badge rec">{esc(d["badge"])}</span>' if d['badge'] == 'Recommended' else (f'<span class="badge">{esc(d["badge"])}</span>' if d['badge'] else '')
    new = '<span class="badge new">New</span>' if d['isNew'] else ''
    return f'''
<section class="dir" id="{slug(d['name'])}">
  <header class="dir-head">
    <div class="dir-meta">{badge}{new}<span class="mono">{idx+1} of {len(finals)}</span></div>
    <h2 class="dir-name" style="font-family:'{esc(disp)}', var(--display)">{esc(d['name'])}</h2>
    <p class="dir-line">{esc(d['oneLiner'])}</p>
  </header>
  <div class="mockups">
    {frame(d['name'] + ' · desktop', d, 'desktop', idx, lazy=idx > 0)}
    {frame(d['name'] + ' · phone', d, 'phone', idx, lazy=idx > 0)}
  </div>
  <div class="glance">
    <div><h3>At a glance</h3><ul>{''.join(f'<li>{md_inline(b)}</li>' for b in d['bullets'][:3])}</ul></div>
    <div><h3>Right for</h3><p>{esc(d['rightForShort'])}</p><h3>Needs from the client</h3><ul class="needs">{''.join(f'<li>{esc(n)}</li>' for n in d['needs'][:4])}</ul></div>
    <div><h3>Palette</h3>{strip(pal)}<h3>Type</h3><p class="typeline"><span style="font-family:'{esc(disp)}', var(--display)">{esc(disp)}</span> <span class="muted">display</span> · <span style="font-family:'{esc(body)}', var(--body)">{esc(body)}</span> <span class="muted">body</span></p></div>
  </div>
  {details(d)}
</section>'''

# ---------- assemble ----------
fams = set()
for d in finals + cuts:
    for k in ('display', 'body'):
        n = font_name(d.get('typography', {}).get(k, ''))
        if n: fams.add(n)
fonts_link = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?' + '&'.join('family=' + n.replace(' ', '+') + ':ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400' for n in sorted(fams)) + '&display=swap">'

n_word = NUMBER_WORDS.get(len(finals), str(len(finals)))
chips = ''.join(f'<a href="#{slug(d["name"])}">{mini(d.get("palette", []), 5)}{esc(d["name"])}</a>' for d in finals)
overview = ''.join(f'''<a class="ov" href="#{slug(d['name'])}">
  <div class="ov-frame"><div class="viewport" style="--w:1200;--h:860"><iframe title="{esc(d['name'])} thumbnail" {('srcdoc="' + esc(fix_fonts(d['desktopHtml'])) + '"') if EMBED else ('src="' + esc(d['desktop']) + '"')} sandbox="allow-same-origin" tabindex="-1"></iframe></div></div>
  <span class="ov-name">{esc(d['name'])}{' <em>new</em>' if d['isNew'] else ''}</span><span class="ov-reg">{esc(d['matrix'].get('register') or d['oneLiner'][:60])}</span>
</a>''' for d in finals)
why = ''.join(f'<div><h3>{esc(w["title"])}</h3><ul>{"".join(f"<li>{md_inline(b)}</li>" for b in w["bullets"])}</ul></div>' for w in DATA['why'])

def cell(d, k):
    v = d['matrix'].get(k)
    if v: return esc(v)
    pal = d.get('palette', []); typ = d.get('typography', {})
    if k == 'ground': return esc((pal[0].get('note') or pal[0].get('role')) if pal else '')
    if k == 'accent': return esc(role_hex(pal, r'accent|primary|cta', ''))
    if k == 'type': return esc(font_name(typ.get('display', '')) + ' / ' + font_name(typ.get('body', '')))
    if k == 'device': return esc((d.get('signatureMoments') or [''])[0][:70])
    if k == 'register': return esc(d.get('oneLiner', '')[:70])
    return ''

rows = ''.join(f'<tr><th scope="row"><a href="#{slug(d["name"])}">{esc(d["name"])}</a>{" <span class=badge>New</span>" if d["isNew"] else ""}</th><td>{mini(d.get("palette", []))} {cell(d,"ground")}</td><td>{cell(d,"accent")}</td><td>{cell(d,"type")}</td><td>{cell(d,"device")}</td><td>{cell(d,"register")}</td><td>{esc(d["rightForShort"])}</td></tr>' for d in finals)

cut_cards = ''.join(f'''<article class="cut-card">
  {frame(d['name'] + ' · first-round hero', d, 'desktop', 100 + j, lazy=True)}
  <h3><span class="mono muted">{esc(d['angle'])}</span> {esc(d['name'])}</h3>
  <p class="small">{esc(d['why'])}</p>
</article>''' for j, d in enumerate(cuts))

rec, ru = DATA['recommendation'], DATA['runnerUp']

page = f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Megaphone Redesign Directions</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700&family=Instrument+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
{fonts_link}
<style>
:root{{
  --bg:#EDEFF1; --surface:#FFFFFF; --ink:#15181D; --muted:#5B6470; --line:#D3D8DE; --line-strong:#B9C1CA;
  --accent:#1D3FD1; --accent-ink:#FFFFFF; --tint:#E4E9FA; --shadow:0 1px 2px rgba(20,24,29,.06), 0 14px 36px -18px rgba(20,24,29,.28);
  --display:'Bricolage Grotesque','Archivo',system-ui,sans-serif; --body:'Instrument Sans','Helvetica Neue',Arial,sans-serif; --mono:'IBM Plex Mono',ui-monospace,Menlo,monospace;
  color-scheme:light;
}}
@media (prefers-color-scheme:dark){{ :root:not([data-theme="light"]){{ --bg:#111417; --surface:#191D22; --ink:#EAEDF1; --muted:#98A2AE; --line:#2B3239; --line-strong:#3A424B; --accent:#8FA3FF; --accent-ink:#0E1330; --tint:#1E2745; --shadow:0 1px 2px rgba(0,0,0,.4), 0 14px 36px -18px rgba(0,0,0,.7); color-scheme:dark; }} }}
:root[data-theme="dark"]{{ --bg:#111417; --surface:#191D22; --ink:#EAEDF1; --muted:#98A2AE; --line:#2B3239; --line-strong:#3A424B; --accent:#8FA3FF; --accent-ink:#0E1330; --tint:#1E2745; --shadow:0 1px 2px rgba(0,0,0,.4), 0 14px 36px -18px rgba(0,0,0,.7); color-scheme:dark; }}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent)}} a:focus-visible,summary:focus-visible{{outline:2px solid var(--accent);outline-offset:3px}}
code{{font-family:var(--mono);font-size:.8em}}
.mono{{font-family:var(--mono);font-size:.72rem;letter-spacing:.04em;text-transform:uppercase}}
.muted{{color:var(--muted)}} .small{{font-size:.9rem;color:var(--muted)}}
.wrap{{max-width:1280px;margin:0 auto;padding-inline:clamp(16px,3vw,40px)}}
h1,h2,h3,h4{{font-family:var(--display);letter-spacing:-.01em;text-wrap:balance;margin:0}}
h3{{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);font-family:var(--mono);font-weight:500;margin:1.2rem 0 .45rem}}
h3:first-child{{margin-top:0}}
p{{margin:0 0 .6rem}} ul{{margin:0 0 .6rem;padding-left:1.1rem}} li{{margin:.3rem 0}}
.badge{{display:inline-block;font-family:var(--mono);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;padding:.18rem .5rem;border-radius:999px;border:1px solid var(--line-strong);color:var(--muted);vertical-align:middle}}
.badge.rec{{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}}
.badge.new{{border-color:var(--accent);color:var(--accent)}}

/* header: chips wrap instead of overflowing */
.bar{{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}}
.bar .wrap{{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem 1rem;padding-block:.55rem}}
.brand{{font-family:var(--display);font-weight:700;white-space:nowrap;font-size:.95rem;line-height:1.1;margin-right:auto}}
.brand small{{display:block;font-family:var(--mono);font-weight:400;font-size:.62rem;color:var(--muted);letter-spacing:.04em;text-transform:uppercase;margin-top:.15rem}}
.chips{{display:flex;flex-wrap:wrap;gap:.35rem}}
.chips a{{display:inline-flex;align-items:center;gap:.4rem;white-space:nowrap;text-decoration:none;color:var(--ink);font-size:.8rem;font-weight:500;padding:.28rem .6rem .28rem .38rem;border:1px solid var(--line);border-radius:999px;background:var(--surface)}}
.chips a:hover{{border-color:var(--line-strong)}}
.chips a.plain{{padding-left:.6rem;color:var(--accent)}}
.mini{{display:inline-flex;height:12px;border-radius:3px;overflow:hidden;border:1px solid rgba(0,0,0,.12);flex:none;vertical-align:middle}}
.mini i{{display:block;width:8px;height:100%}}

/* intro */
.intro{{padding-block:clamp(2rem,5vw,4rem) 1.5rem}}
.intro h1{{font-size:clamp(2.2rem,5.4vw,4.4rem);line-height:1;font-weight:600;letter-spacing:-.03em;max-width:16ch}}
.intro .lede{{font-size:1.05rem;max-width:64ch;margin-top:1rem}}
.overview{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:.9rem;margin-top:1.8rem}}
.ov{{text-decoration:none;color:var(--ink);display:grid;gap:.3rem;align-content:start}}
.ov-frame{{border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff;box-shadow:var(--shadow)}}
.ov-name{{font-family:var(--display);font-weight:600;font-size:.95rem;margin-top:.2rem}}
.ov-name em{{font-style:normal;font-family:var(--mono);font-size:.62rem;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);margin-left:.3rem}}
.ov-reg{{font-size:.76rem;color:var(--muted);line-height:1.3}}
.why{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:2rem;padding-block:1.5rem 2.5rem;border-top:1px solid var(--line);margin-top:2rem}}
.why li{{font-size:.95rem}}

/* direction */
.dir{{border-top:1px solid var(--line-strong);padding-block:2.2rem 2.8rem;scroll-margin-top:110px}}
.dir-head{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:.4rem 3rem;align-items:end;margin-bottom:1rem}}
.dir-meta{{grid-column:1/-1;display:flex;align-items:center;gap:.6rem;color:var(--muted)}}
.dir-name{{font-size:clamp(2.2rem,5.5vw,4.2rem);line-height:.98;font-weight:600;letter-spacing:-.02em}}
.dir-line{{font-size:1.05rem;max-width:40ch;margin:0;color:var(--muted);text-wrap:balance}}
.mockups{{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:1rem;align-items:start;margin-bottom:1.4rem}}
.frame{{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden;box-shadow:var(--shadow)}}
.chrome{{display:flex;align-items:center;gap:.7rem;padding:.45rem .75rem;border-bottom:1px solid var(--line);font-family:var(--mono);font-size:.66rem;color:var(--muted)}}
.dots{{display:inline-flex;gap:4px}} .dots i{{width:7px;height:7px;border-radius:50%;background:var(--line-strong);display:block}}
.chrome .url{{background:var(--bg);border-radius:6px;padding:.2rem .7rem;flex:1;text-align:center;max-width:400px;margin-inline:auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.chrome .tag{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:40%}}
.frame.phone .chrome .url{{display:none}} .frame.phone .chrome .tag{{max-width:100%;margin-left:auto}}
.viewport{{position:relative;width:100%;overflow:hidden;background:#fff;--s:1;height:calc(var(--h)*1px*var(--s))}}
.viewport iframe{{position:absolute;inset:0;width:calc(var(--w)*1px);height:calc(var(--h)*1px);border:0;transform-origin:0 0;transform:scale(var(--s));background:#fff;pointer-events:none}}
.glance{{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:2rem;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:1.1rem 1.3rem}}
.glance li,.glance p{{font-size:.95rem}}
.needs li{{font-size:.9rem}}
.strip{{display:flex;flex-wrap:wrap;gap:.45rem}}
.sw{{display:grid;gap:.15rem;justify-items:center}} .sw i{{display:block;width:34px;height:34px;border-radius:8px;border:1px solid rgba(0,0,0,.12)}} .sw code{{font-size:.6rem;color:var(--muted)}}
.typeline{{font-size:1rem}}
.more{{margin-top:.9rem}} .more summary{{cursor:pointer;font-family:var(--mono);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:.4rem 0}}
.more-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.4rem 2rem;padding:1rem 0 .5rem;font-size:.92rem}}
.more-grid h4{{font-family:var(--mono);font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 .4rem;font-weight:500}}
.more-grid p,.more-grid li{{max-width:60ch}}

/* compare, verdict, cut */
.sec{{border-top:1px solid var(--line-strong);padding-block:2.5rem}}
.sec h2{{font-size:clamp(1.6rem,3.2vw,2.4rem);font-weight:600;letter-spacing:-.02em;margin-bottom:1rem}}
.tablewrap{{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:12px}}
table{{border-collapse:collapse;width:100%;min-width:960px;font-size:.88rem}}
th,td{{text-align:left;vertical-align:top;padding:.7rem .9rem;border-bottom:1px solid var(--line)}}
thead th{{font-family:var(--mono);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500}}
tbody th{{font-weight:600;white-space:nowrap}} tbody tr:last-child td,tbody tr:last-child th{{border-bottom:0}}
.verdict{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}}
.pick{{background:var(--tint);border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);border-radius:12px;padding:1.2rem 1.4rem}}
.pick h3{{color:var(--accent)}} .pick .name{{font-family:var(--display);font-size:1.7rem;font-weight:600;letter-spacing:-.02em;margin-bottom:.4rem}}
.pick.second{{background:var(--surface);border-color:var(--line)}} .pick.second h3{{color:var(--muted)}}
.before{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:2rem}}
.before li{{font-size:.95rem}}
.cut-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.4rem}}
.cut-card h3{{font-family:var(--display);text-transform:none;letter-spacing:-.01em;font-size:1.15rem;color:var(--ink);margin:.5rem 0 .15rem;display:flex;gap:.5rem;align-items:baseline}}
.cut-card h3 .mono{{font-size:.62rem}} .cut-card .frame{{margin-bottom:.3rem}}
footer{{border-top:1px solid var(--line);padding-block:1.5rem 3rem;font-size:.85rem;color:var(--muted);max-width:80ch}}
@media (max-width:1000px){{ .mockups{{grid-template-columns:minmax(0,1fr) 190px}} .glance{{grid-template-columns:1fr 1fr}} }}
@media (max-width:760px){{
  .intro h1{{max-width:none}} .why,.glance,.verdict,.before,.dir-head{{grid-template-columns:1fr}}
  .mockups{{grid-template-columns:1fr}} .frame.phone{{max-width:280px}} .dir{{scroll-margin-top:150px}}
}}
@media (prefers-reduced-motion:no-preference){{ html{{scroll-behavior:smooth}} }}
</style>

<div class="bar"><div class="wrap">
  <div class="brand">Nonprofit Megaphone<small>Redesign directions · {esc(DATA['date'])}</small></div>
  <nav class="chips" aria-label="Directions">{chips}<a class="plain" href="#compare">Compare</a><a class="plain" href="#verdict">Verdict</a></nav>
</div></div>

<main class="wrap">
  <section class="intro">
    <h1>Same megaphone, {n_word} different voices.</h1>
    <p class="lede">{esc(DATA['lede'])}</p>
    <div class="overview">{overview}</div>
  </section>
  <section class="why">{why}</section>

  {''.join(chapter(d, i) for i, d in enumerate(finals))}

  <section class="sec" id="compare">
    <h2>Side by side</h2>
    <div class="tablewrap"><table>
      <thead><tr><th>Direction</th><th>Ground</th><th>Accent</th><th>Type</th><th>Signature device</th><th>Register</th><th>Right for</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
  </section>

  <section class="sec" id="verdict">
    <h2>Verdict</h2>
    <div class="verdict">
      <div class="pick"><h3>Recommended</h3><p class="name">{esc(rec['name'])}</p><ul>{''.join(f'<li>{md_inline(b)}</li>' for b in rec['bullets'])}</ul></div>
      <div class="pick second"><h3>Runner-up</h3><p class="name">{esc(ru['name'])}</p><ul>{''.join(f'<li>{md_inline(b)}</li>' for b in ru['bullets'])}</ul></div>
    </div>
    <p class="small" style="margin-top:.9rem">The verdict covers the five judged directions. The {len(DATA.get('new', []))} newer ones marked <span class="badge new">New</span> were added afterwards as alternatives and have not been through the judging panel.</p>
  </section>

  <section class="sec">
    <h2>Before you choose</h2>
    <div class="before">
      <div><h3>Every direction includes</h3><ul>{''.join(f'<li>{md_inline(x)}</li>' for x in DATA['evidence'])}</ul></div>
      <div><h3>Decisions that shape the build</h3><ul>{''.join(f'<li>{md_inline(x)}</li>' for x in DATA['decisions'])}</ul></div>
      <div><h3>Not in this pitch yet</h3><ul>{''.join(f'<li>{md_inline(x)}</li>' for x in DATA['notYet'])}</ul></div>
    </div>
  </section>

  <section class="sec">
    <h2>Also explored</h2>
    <div class="cut-grid">{cut_cards}</div>
  </section>
</main>
<footer class="wrap">Every mockup is HTML and CSS rendered live, not an image, using free fonts. Figures are the company's own: 780+ nonprofits, $48M+ managed, 60+ staff, a written 100% grant-acquisition guarantee, one of nine inaugural Google Ad Grants Certified Professional agencies, and the endorsement of Google's first Head of Ad Grants.</footer>

<script>
(function(){{
  var vps = document.querySelectorAll('.viewport');
  function fit(){{ vps.forEach(function(v){{ var w = v.clientWidth || v.getBoundingClientRect().width; var base = parseFloat(getComputedStyle(v).getPropertyValue('--w')) || 1200; v.style.setProperty('--s', (w/base).toFixed(4)); }}); }}
  if ('ResizeObserver' in window) {{ var ro = new ResizeObserver(fit); vps.forEach(function(v){{ ro.observe(v); }}); }}
  window.addEventListener('resize', fit); fit();
}})();
</script>
'''

if EMBED:
    out = os.path.join(ROOT, 'tools', 'pitch-standalone.html')
    page = page.replace('<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n', '<meta charset="utf-8">\n', 1)
else:
    out = OUT
    page = '<!doctype html>\n<html lang="en">\n<head>\n' + page.split('<style>')[0] + '<style>' + page.split('<style>', 1)[1].split('</style>')[0] + '</style>\n</head>\n<body>\n' + page.split('</style>', 1)[1] + '\n</body>\n</html>\n'
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write(page)
print('wrote', out, len(page), 'bytes;', len(finals), 'directions,', len(cuts), 'first-round')
