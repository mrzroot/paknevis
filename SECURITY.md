# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ |

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Instead, use
GitHub's private reporting: **Security → Report a vulnerability** on
<https://github.com/mrzroot/paknevis/security/advisories/new>.

Include a description, a minimal reproduction (input text/file and command)
and the paknevis version (`paknevis --version`). You can expect an initial
reply within a week. Fixes are released as patch versions and credited in the
changelog unless you prefer otherwise.

## Scope and threat model

- paknevis reads and (with `fix`) rewrites the local files you pass to it. It
  never executes file contents and performs no network access.
- YAML dictionaries are parsed with `yaml.safe_load`; TOML with the standard
  library parser.
- The regular expressions used by rules are written to run in linear time on
  typical input; inputs that cause pathological slowdowns (ReDoS) are
  considered security bugs — please report them.
- The browser playground runs entirely client-side. It loads the Pyodide
  runtime from the jsDelivr CDN and the paknevis bundle from GitHub Pages; no
  text you type is sent anywhere.
