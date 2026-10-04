# Verification record

This file states plainly what was actually run and verified during
development of this delivery, versus what could not be verified in the
sandboxed build environment used to write it, so nothing here is overstated.

Environment: Ubuntu 24.04 container, Python 3.12.3, network access limited to
PyPI, GitHub, and Ubuntu's package mirrors (no general internet access, no
Docker daemon).

## ✅ Actually verified

| What | How |
|---|---|
| All 95 tests pass | `pytest tests/ -v --cov=sentryx` — ran directly, output captured |
| DB layer (`db.py`) correctness | Tested against a **real PostgreSQL 16** instance installed via `apt-get install postgresql`, not mocked. Migration applied with `psql -f migrations/001_init.sql` against a fresh database with no errors. |
| `flake8` clean | Ran directly against `src/` and `tests/` |
| `black --check` clean | Ran directly |
| `mypy` clean | Ran directly against `src/sentryx/` (strict enough to catch the Anthropic SDK / requests typing mismatches that were then fixed) |
| `bandit` clean | Ran directly; the 2 genuine low-severity findings (subprocess usage) are suppressed with `# nosec` comments explaining why they're safe (validated input, no `shell=True`) rather than blanket-ignored |
| `pip-audit` clean | Ran directly against pinned `requirements.txt` — no known CVEs in the pinned versions as of 2026-10-04 |
| Dependency versions | Every pin in `requirements.txt` / `requirements-dev.txt` was checked against PyPI's actual latest stable release (`pip index versions`), not recalled from training data |
| `pip install -r requirements-dev.txt` | Ran directly, no conflicts, full dependency tree resolved |
| Recon tool installability | `nmap`, `whois`, `whatweb`, `dnsutils` (dig), `curl`, `nikto` were **actually installed** via `apt-get` on Ubuntu 24.04 and their version/help output captured — this is also what the Dockerfile installs |
| Command-injection resistance | `validators.py` tested against 15+ real malicious payloads (`; rm -rf /`, backticks, `$()`, leading-dash flag injection, etc.) — all rejected |
| HTML-escaping in reports | Tested with an actual `<script>` payload as a finding name — confirmed escaped in output |

## ❌ Not verified (and why)

| What | Why not | What to do instead |
|---|---|---|
| `docker build` / full container boot | No Docker daemon available in the build sandbox | Run `docker build -t sentryx:0.1.0 .` yourself before relying on the image; the CI workflow's `docker-build` job will do this automatically on GitHub's runners |
| Live Claude API calls | No API key provisioned in the sandbox, and doing so would have required your credentials | `llm.py` is tested with the Anthropic SDK fully mocked (request/response shapes match SDK 1.11.0's actual types, verified via `mypy`); run a real `sentryx scan` with your own `ANTHROPIC_API_KEY` to validate the live path |
| Live NVD CVE lookups | `search.py` is tested with `requests` mocked, not a live call to `nvd.nist.gov` | Works the same way live, but you should sanity-check one real lookup before depending on it |
| Actual nmap/nikto scans against a real target | No authorized target was provided, and scanning anything without explicit authorization is both against policy and, depending on the target, illegal | Run `sentryx scan --target scanme.nmap.org --authorization-ref "..."` — nmap.org explicitly permits scanning that host |
| WeasyPrint PDF rendering | Installed and importable, but `render_pdf_report()` itself wasn't exercised end-to-end in a test | Covered indirectly by `render_html_report` tests (same template path); run `sentryx report --format pdf` once locally to confirm |
| CI workflow execution | `.github/workflows/ci.yml` is syntactically valid YAML and mirrors exactly the commands run manually above, but GitHub Actions itself never executed it | Push to a real repo and watch the first run |
| Code signing / signed releases | No signing keys exist for this project | Add a `cosign`/GPG step to CI if you need attestable release artifacts |
| IAM / cloud deployment | No deployment target was specified | Out of scope until you pick a target (AWS/GCP/on-prem) |

## Bottom line

Everything in the "actually verified" table was run, not assumed, inside
this build session. Everything in the second table is real, complete code
that follows the same patterns as the verified parts, but needs one more
pass with your own credentials, a Docker daemon, and (for the scan path) an
authorized target before you treat it as production-proven.
