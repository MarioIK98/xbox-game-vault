#!/usr/bin/env python3
"""Deterministic, allowlisted static release. Preview never becomes a business launch."""
from __future__ import annotations
import argparse, hashlib, html, json, re, shutil, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SOURCE = 'https://marioik98.github.io/xbox-game-vault/'
ROOT_FILES = ('index.html', 'sitemap.xml')
BASE_PUBLIC_FILES = (
    'index.html', 'uebersicht.html', 'teilen.html', 'datenschutz.html',
    'hinweise.html', 'sw.js', 'sitemap.xml', 'robots.txt',
    'site.webmanifest', 'og-game-vault.jpg',
    'icons/game-vault-192.png', 'icons/game-vault-512.png',
    'plattform/xbox-360.html', 'plattform/original-xbox.html',
    'plattform/playstation-2.html', 'plattform/psp.html',
    'plattform/playstation-4.html', 'plattform/playstation-5.html',
    'plattform/nintendo-ds.html', 'plattform/pc.html',
    'reichweite/beitraege.txt', 'reichweite/links.json',
    'reichweite/feed.xml',
)
PUBLIC_FILES = (*BASE_PUBLIC_FILES, 'spiele-sammlung.html',
    *(f'spiele/{p.name}' for p in sorted((ROOT/'oeffentlich/spiele').glob('*.html'))))
TEXT_EXT = {'.html', '.xml', '.json', '.txt', '.js', '.webmanifest'}
BLOCK = re.compile(r'<!-- GV_SECURITY_START -->.*?<!-- GV_SECURITY_END -->\s*', re.S)
SCRIPTS = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)

def approved_production(host: str) -> None:
    policy = json.loads((ROOT / 'release/hosting_policy.json').read_text(encoding='utf-8'))
    conf = policy['commercial_hosting']
    required = (
        policy['release_intent'] == 'commercial_launch',
        policy['current_host'] == 'render',
        conf['status'] == 'APPROVED',
        conf['provider'] == 'render',
        conf['account_access_verified'] is True,
        conf['commercial_terms_verified'] is True,
        conf['costs_approved_by_mario'] is True,
        bool(conf.get('plan')),
        bool(conf.get('evidence')),
        host != 'marioik98.github.io',
    )
    if not all(required):
        raise ValueError('STOP: commercial Render deployment lacks verified account, terms and explicit approval')

def validated_origin(value: str) -> str:
    u = urlparse(value)
    if u.scheme != 'https' or not u.hostname or u.username or u.password or u.port or u.query or u.fragment or u.path not in ('', '/'):
        raise ValueError('Production requires a clean HTTPS site origin, without path or credentials')
    if not re.fullmatch(r'[a-zA-Z0-9.-]+', u.hostname) or '.' not in u.hostname:
        raise ValueError('Invalid origin hostname')
    return f'https://{u.hostname}/'

def security_policy(text: str) -> str:
    import base64
    hashes = sorted({"'sha256-" + base64.b64encode(hashlib.sha256(s.encode('utf-8')).digest()).decode() + "'" for s in SCRIPTS.findall(text)})
    return '; '.join([
        "default-src 'none'", "base-uri 'none'", "object-src 'none'", "frame-src 'none'",
        "form-action 'none'", 'script-src ' + (' '.join(hashes) or "'none'"),
        "script-src-attr 'none'", "style-src 'self' 'unsafe-inline'", "img-src 'self' data:",
        "font-src 'self'", "connect-src 'self'", "manifest-src 'self'",
        "worker-src 'self'", "media-src 'none'",
    ])

def rewrite_meta(text: str, preview: bool) -> str:
    if text.count('GV_SECURITY_START') != 1 or text.count('GV_SECURITY_END') != 1:
        raise ValueError('Expected exactly one existing CSP block')
    text = BLOCK.sub('', text, count=1)
    marker = '<!-- GV_SECURITY_START --><meta http-equiv="Content-Security-Policy" content="' + html.escape(security_policy(text), quote=True) + '"><meta name="referrer" content="no-referrer"><!-- GV_SECURITY_END -->\n'
    m = re.search(r'<meta\s+charset=[^>]+>', text, re.I)
    if not m: raise ValueError('Missing charset for HTML')
    text = text[:m.end()] + marker + text[m.end():]
    if preview:
        replacement = '<meta name="robots" content="noindex,nofollow">'
        pattern = re.compile(r'<meta\s+name=["\']robots["\'][^>]*>', re.I)
        if pattern.search(text):
            text = pattern.sub(replacement, text)
        else:
            text = text.replace('</head>', replacement + '</head>', 1)
    return text

def build(mode: str, origin: str | None, dest: Path) -> dict:
    if mode == 'production':
        if not origin: raise ValueError('Production requires --origin')
        replacement = validated_origin(origin)
        approved_production(urlparse(replacement).hostname)
    elif origin:
        raise ValueError('Preview does not accept a production origin')
    else:
        replacement = PUBLIC_SOURCE
    # Reject symlinks before path resolution to avoid deleting anything outside dist.
    dest = dest.absolute()
    if dest != (ROOT / 'dist').absolute():
        raise ValueError('Only the repository-local dist directory may be replaced')
    if dest.is_symlink():
        raise ValueError('Refusing to follow a symlinked output directory')
    if dest.exists():
        shutil.rmtree(dest)
    manifest = []
    for rel in [*ROOT_FILES, *('oeffentlich/' + name for name in PUBLIC_FILES)]:
        src = ROOT / rel
        if not src.is_file() or src.is_symlink():raise ValueError('Required regular source file missing: ' + rel)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        if target.suffix in TEXT_EXT:
            text = data.decode('utf-8')
            if mode == 'production':
                text = text.replace(PUBLIC_SOURCE, replacement)
            if target.suffix == '.html':
                text = rewrite_meta(text, mode == 'preview')
            data = text.encode('utf-8')
        target.write_bytes(data)
        manifest.append({'path': rel, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    robots = ("User-agent: *\nDisallow: /\n" if mode == 'preview'
              else "User-agent: *\nAllow: /oeffentlich/\nSitemap: " + replacement + 'sitemap.xml\n')
    (dest/'robots.txt').write_text(robots, encoding='utf-8')
    (dest/'oeffentlich/robots.txt').write_text(robots, encoding='utf-8')
    manifest = [r for r in manifest if r['path'] != 'oeffentlich/robots.txt']
    newdata = (dest/'oeffentlich/robots.txt').read_bytes()
    manifest.append({'path': 'oeffentlich/robots.txt', 'sha256': hashlib.sha256(newdata).hexdigest(), 'bytes': len(newdata)})
    data = (dest/'robots.txt').read_bytes()
    manifest.append({'path': 'robots.txt', 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    report = {
        'project': 'MarioIK98/xbox-game-vault',
        'mode': mode,
        'indexable': mode == 'production',
        'origin': replacement,
        'files': sorted(manifest, key=lambda x: x['path']),
        'production_ready': mode == 'production',
        'advertisers_approved_by_this_step': False,
        'notes': 'This is a static allowlisted distribution, not a WAF or a commercial deployment on its own.',
    }
    (dest/'build-manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n',encoding='utf-8')
    return report

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['preview','production'], default='preview')
    ap.add_argument('--origin')
    ap.add_argument('--dest', default='dist')
    args = ap.parse_args()
    try:
        report = build(args.mode, args.origin, (ROOT/args.dest) if not Path(args.dest).is_absolute() else Path(args.dest))
    except (ValueError, OSError) as e:
        print('BUILD STOPPED:', e, file=sys.stderr)
        return 2
    print(json.dumps({k: v for k,v in report.items() if k != 'files'} | {'files':len(report['files'])}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':sys.exit(main())
