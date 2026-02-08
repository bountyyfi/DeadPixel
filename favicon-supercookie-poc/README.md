# Dead Pixel - Favicon Attack Surface Research

This repository documents three novel attack vectors abusing browser favicon behavior. Favicons are one of the most overlooked elements in web security - no SAST, DAST, or SCA tool inspects favicon URLs or behavior.

> ⚠️ **Security research for defensive purposes.** All domains, endpoints, and infrastructure are fictional or localhost-only. No malicious infrastructure exists. Published by [Bountyy Oy](https://bountyy.fi), a Finnish cybersecurity consultancy.

## TL;DR

| Attack | Impact | Detected by scanners? |
|---|---|---|
| **Favicon Supercookie** | Cross-site tracking surviving cookie clearing, incognito, VPN | ❌ No |
| **Internal Network Scanner** | Enumerate internal hosts from external website | ❌ No |
| **AI-Assisted Favicon Injection** | Poisoned docs trick AI into wiring attacker favicon into production | ❌ No |

## Why "Dead Pixel"?

A dead pixel on your screen - you don't notice it, you can't fix it, and it's always watching. That's what a weaponized favicon is. A 16x16 image that fires on every page load, carries credentials, bypasses CORS, ignores ad blockers, survives cookie clearing, and no security tool on earth flags it.

## Attack 1: Favicon Supercookie

Browsers maintain a **separate cache for favicons** that in some implementations is not fully partitioned by top-level site. This enables a tracking supercookie that:

- Survives cookie and localStorage clearing
- Works across incognito boundary in some browsers
- Survives VPN and IP changes
- Persists across browser restarts
- Requires no JavaScript on the tracking page

### How it works

1. First visit: server generates a **unique favicon per user** - a 32x32 BMP where pixel data encodes a tracking ID
2. Favicon is served with aggressive cache headers (`Cache-Control: max-age=31536000, immutable`)
3. On subsequent visits (even different sites), the server detects cache hits vs misses
4. By probing multiple cached favicon URLs, the server reconstructs the tracking ID without cookies

### See: [`supercookie/`](supercookie/)

Run the PoC:
```bash
cd supercookie
python3 server.py
# Visit http://localhost:8080/track?debug=1 to set
# Visit http://localhost:8080/probe to read back
```

## Attack 2: Internal Network Favicon Scanner

Favicon requests are **credentialed by default** and **not subject to CORS preflight**. An external website can probe internal network hosts:

```html
<link rel="icon" href="https://jira.corp.local/favicon.ico">
```

By measuring timing and error behavior, the attacker determines:
- Whether internal hosts exist
- Whether the user has network access to them
- Whether the user is authenticated (based on response patterns)

### See: [`network-scanner/`](network-scanner/)

Open `scanner.html` in a browser on a corporate network to see which internal hosts are reachable.

## Attack 3: AI-Assisted Favicon Injection

Combines with our [invisible-prompt-injection](https://github.com/bountyyfi/invisible-prompt-injection) research. A fake npm package `dead-pixel` (a "RUM monitoring library") has a clean README that renders normally. Hidden in HTML comments and markdown reference links:

- Favicon beacon URLs pointing to attacker infrastructure
- `<link rel="preconnect">` to attacker domains
- Docker ENV vars for attacker collector endpoints
- `<meta>` tags for project identification

When a developer asks AI to "set up dead-pixel in production," the AI reads the raw markdown, finds the hidden "documentation," and generates production code with attacker beacons baked in.

### See: [`ai-injection/`](ai-injection/)

- `poisoned-readme.md` - the fake library docs (view raw to see hidden payloads)
- `expected-ai-output.md` - what AI actually generates

## Why No Scanner Catches This

| Tool | What it checks | Favicons? |
|------|---------------|-----------|
| **SAST** | Code logic, data flow | ❌ Doesn't analyze `<link rel="icon">` |
| **DAST** | Endpoints, responses, injections | ❌ Doesn't test favicon cache behavior |
| **SCA** | Dependency vulnerabilities | ❌ Favicons aren't dependencies |
| **CSP** | Content policy enforcement | ❌ Most policies don't restrict favicon origins |
| **WAF** | Request patterns, payloads | ❌ Favicon requests are normal HTTP |
| **Ad blockers** | Known tracker domains, scripts | ❌ Favicons are exempt |
| **Code review** | Logic, security patterns | ❌ Nobody reviews favicon URLs |
| **npm audit** | Known vulnerable packages | ❌ README content not scanned |

## Repository Contents

```
dead-pixel/
├── README.md                              ← You are here
├── supercookie/
│   ├── server.py                          ← Tracking server (unique favicon per user)
│   ├── tracker.html                       ← Sets the supercookie
│   └── probe.html                         ← Reads it back (cache timing)
├── network-scanner/
│   ├── scanner.html                       ← Internal host enumeration
│   └── targets.js                         ← Common internal hostnames
├── ai-injection/
│   ├── poisoned-readme.md                 ← Fake "dead-pixel" library docs
│   └── expected-ai-output.md              ← What AI generates
└── LICENSE
```

## Defenses

### For browser vendors (highest priority)
1. **Fully partition favicon cache by top-level site**
2. **Strip credentials from cross-origin favicon requests**
3. **Apply CORS or CSP enforcement to `<link rel="icon">` loads**

### For AI tool developers
1. **Render markdown before LLM processing** - strip HTML comments and reference links
2. **Treat all documentation as untrusted input**
3. **Flag `<link>`, `<script>`, and URL patterns in AI-generated HTML**

### For developers
1. **Explicitly set your favicon** - don't rely on convention or AI suggestions
2. **Add `img-src` to CSP** and restrict to your own origins
3. **Audit AI-generated `<link>` and `<meta>` tags** - verify every external URL
4. **Review ENV vars** AI suggests for Docker deployments

### For platforms (GitHub, npm, PyPI)
1. **Show HTML comment indicators** on rendered READMEs
2. **Offer rendered-only API** for AI tool consumption
3. **Scan for URLs in HTML comments** - instructional patterns in hidden content are suspicious

## Related Research

- [Invisible Prompt Injection](https://github.com/bountyyfi/invisible-prompt-injection) - our prior research on hidden markdown injection
- [Lonkero](https://github.com/bountyyfi/lonkero) - our vulnerability scanner that detects hidden prompt injection patterns

## Responsible Disclosure

This research is published for defensive awareness. All demonstrated techniques use fictional infrastructure.

- **Author:** Mihalis Haatainen ([@bountyy](https://bountyy.fi))
- **Organization:** Bountyy Oy, Finland
- **Contact:** [info@bountyy.fi](mailto:info@bountyy.fi)

## License

MIT © 2026 Bountyy Oy
