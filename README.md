# iplookup.py

A command-line IP geolocation and ISP lookup tool with a hacker-style terminal UI. Supports single lookups, batch lookups from a file, JSON/CSV export, and scriptable (piped) output.

<img width="2048" height="768" alt="image" src="https://github.com/user-attachments/assets/62a92d88-850f-494a-8cb7-0462f2aa9c09" />

## Features

- **Single or batch lookups** — pass one or more IPs directly, read them from a file, or get prompted interactively.
- **Rich target info** — shows IP, country, region, city, zip, timezone, ISP, organization, ASN, and coordinates by default.
- **Verbose mode** — reveals any additional fields the API returns beyond the standard set, plus request/response details (URL, status code, timing, rate-limit headers).
- **JSON mode** — prints raw JSON only, with all decoration (banner, colors, animations) suppressed, so it's safe to pipe or redirect.
- **Export** — save results to `.json`, `.csv`, or plain text, chosen automatically by the output file's extension.
- **Rate-limit aware** — stops the batch early and reports clearly if the API key is rejected or the daily limit is hit, instead of burning through remaining targets.
- **Terminal-friendly** — animations and colors auto-disable when output is piped or redirected, or can be turned off manually.

## Requirements

- Python 3.8+
- [`requests`](https://pypi.org/project/requests/)

Install dependencies:

```bash
pip install requests
```

## API Key

This tool requires an API key for `wimi-api.whatismyip.com`.

Set it as an environment variable (recommended — keeps it out of your shell history):

```bash
export WIMI_API_KEY="your-key-here"
```

Or pass it directly with `-k` / `--key` (less safe, but available if needed):

```bash
python iplookup.py -t 8.8.8.8 -k your-key-here
```

## Usage

```bash
python iplookup.py [-t IP [IP ...]] [-f FILE] [-o FILE] [-v] [-j]
                    [-d SEC] [--timeout SEC] [-k KEY] [--no-fx] [--no-color]
```

### Arguments

| Flag | Long form | Description |
|------|-----------|--------------|
| `-t`, `-i` | `--target`, `--ip` | One or more IP addresses to look up. |
| `-f` | `--file` | Read IPs from a file, one per line (`#` lines are treated as comments). |
| `-o` | `--output` | Save results to a file. Format is picked from the extension: `.json`, `.csv`, or plain text otherwise. |
| `-v` | `--verbose` | Show extra fields and request details (URL, status, timing, rate-limit headers). |
| `-j` | `--json` | Print results as raw JSON only — no banner, colors, or effects. Ideal for piping. |
| `-d` | `--delay` | Seconds to wait between batch lookups (default: `1.0`). |
| | `--timeout` | Request timeout in seconds (default: `15`). |
| `-k` | `--key` | API key. Overrides `WIMI_API_KEY`. Prefer the environment variable — keys passed here can end up in shell history. |
| | `--no-fx` | Skip the typing effect and progress bars. |
| | `--no-color` | Disable colored output. |
| `-V` | `--version` | Show the tool's version and exit. |

If no target is given and `-j`/`--json` isn't set, you'll be prompted interactively for an IP.

### Examples

**Single lookup:**

```bash
python iplookup.py -t 8.8.8.8
```

**Multiple IPs, verbose:**

```bash
python iplookup.py -t 8.8.8.8 1.1.1.1 -v
```

**Batch lookup from a file, save as CSV, no animations:**

```bash
python iplookup.py -f ips.txt -o results.csv --no-fx
```

**Scriptable JSON output, redirected to a file:**

```bash
python iplookup.py -t 8.8.8.8 --json > result.json
```

## How it works

1. Parses CLI arguments and resolves runtime settings (verbose, JSON-only mode, animations, color).
2. Confirms an API key is available (`-k` or `WIMI_API_KEY`); exits with an error if neither is set.
3. Gathers and validates targets from `-t`, `-f`, or an interactive prompt — invalid or duplicate IPs are skipped with a warning.
4. For each target, sends a request to the lookup API and handles the response:
   - `429` → stops the remaining batch early (rate limit reached).
   - `401` / `403` → stops the batch early (API key rejected).
   - Other errors → reported per-target; the batch continues.
   - Success → result is displayed in a bordered summary box and added to the results list.
5. Waits `--delay` seconds between lookups when running a batch.
6. If `-j` is set, prints the full result set as JSON at the end.
7. If `-o` is set, writes all collected results to the specified file.
8. Exits with status `0` if every lookup succeeded, or `1` if any failed.

## Output fields

Shown by default for every result:

- IP address
- Country
- Region
- City
- Zip code
- Timezone
- ISP
- Organization
- ASN
- Latitude / Longitude

With `-v`/`--verbose`, any additional fields returned by the API beyond this list are also shown.

## Notes & Limitations

- Lookups run **sequentially**, with a configurable delay between them — there's no concurrent/threaded mode.
- Field names shown by default assume a typical IP-geolocation API response shape; if the live API uses different key names for some fields, those rows will show `N/A` rather than failing.
- Animations (`--no-fx`) and colors (`--no-color`) are automatically disabled when output is piped, redirected, or `NO_COLOR` is set in the environment — this keeps piped/JSON output clean by default.

## Author

SwiftGlitxh
