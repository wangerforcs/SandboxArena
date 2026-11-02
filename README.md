# Sandbox Arena

Workload-based benchmarks for agent sandboxes.

The project measures complete tasks instead of isolated API timings. A result can include provisioning time, execution time, success rate, tail latency, retries, and estimated cost.

## Quick start

Requires Python 3.10 or later. The current framework has no runtime dependencies.

```bash
cd SandboxArena

python -m arena list-workloads

python -m arena run \
  --provider mock \
  --workload python-smoke \
  --repetitions 3 \
  --output /tmp/arena-result.json

python -m arena validate /tmp/arena-result.json
```

The `mock` provider runs the workload locally. It is only for testing the runner and result format; it is not a sandbox performance result.

## Repository layout

```text
arena/                         CLI, result validation, and provider interfaces
  providers/                   Provider adapters
workloads/                     Versioned workload definitions
schemas/                       Public JSON schemas
data/results/                  Reviewed benchmark results
scripts/                       Build scripts for the website
web/                           Static website
tests/                         Local tests
.github/                       PR templates and GitHub Actions workflows
```

## Adding a result

Result files should use this naming pattern:

```text
data/results/<provider>-<workload>-<date>-<short-id>.json
```

Run a workload and validate the result before opening a pull request:

```bash
python -m arena run \
  --provider mock \
  --workload python-smoke \
  --repetitions 10 \
  --region local \
  --output data/results/mock-local-python-smoke-20261102-example.json

python -m arena validate \
  data/results/mock-local-python-smoke-20261102-example.json
```

Do not commit API keys, tokens, environment variable dumps, private repository contents, or other sensitive data.

Provider adapters are not included yet. Use [`arena/providers/base.py`](arena/providers/base.py) as the starting point for a new adapter.

## Result provenance

Every result must include a `provenance.source` value:

- `self-run`: produced with this repository's runner;
- `community-run`: submitted by a community member;
- `vendor-reported`: provided or confirmed by the vendor;
- `official-claim`: taken from official product material and not independently verified.

The website keeps these sources separate. They should not be presented as equivalent evidence.

## GitHub Pages

The website is plain HTML, CSS, and JavaScript. On every push to `main` or `master`, [the Pages workflow](.github/workflows/deploy-pages.yml) builds `web/data/results.json` from `data/results/*.json` and deploys the `web/` directory.

Enable it once in the repository settings:

```text
Settings → Pages → Build and deployment → Source → GitHub Actions
```

For a repository named `SandboxArena`, the default URL is:

```text
https://<username>.github.io/SandboxArena/
```

Preview the site locally:

```bash
python scripts/build_site_data.py
python -m http.server 4173 --directory web
```

Then open <http://localhost:4173/>.

## Development

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

