# IP Lookup

<img width="661" height="470" alt="image" src="https://github.com/user-attachments/assets/d712835d-c0c7-4d71-9ea9-226d37e414ec" />

A hacker-style command-line tool that looks up an IP address and shows its country, city and ISP, wrapped in a green terminal UI with an ASCII banner, typing effects and progress bars.

**Author:** SwiftGlitxh | **Version:** 1.1.0

```
 ___ ____    _     ___   ___  _  ___   _ ____
|_ _|  _ \  | |   / _ \ / _ \| |/ / | | |  _ \
 | || |_) | | |  | | | | | | | ' /| | | | |_) |
 | ||  __/  | |__| |_| | |_| | . \| |_| |  __/
|___|_|     |_____\___/ \___/|_|\_\\___/|_|
```

## Features

- Validates IPv4 and IPv6 addresses before sending any request
- Returns IP, country, city and ISP
- Green terminal theme with a typewriter effect and progress bars
- Works with a `-t` flag or prompts you interactively
- Handles rate limits, network errors and bad responses cleanly
- API key is read from an environment variable, never hardcoded

## Requirements

- Python 3.7+
- [`requests`](https://pypi.org/project/requests/)
- A free API key from [WhatIsMyIP](https://www.whatismyip.com/)

## Installation

```bash
git clone https://github.com/SwiftGlitxh/ip-lookup.git
cd ip-lookup
pip install requests
```

## Setup

Set your API key as an environment variable so it never ends up in your code or your git history.

**Linux / macOS**

```bash
export WIMI_API_KEY="your-api-key"
```

**Windows (cmd)**

```cmd
set WIMI_API_KEY=your-api-key
```

**Windows (PowerShell)**

```powershell
$env:WIMI_API_KEY="your-api-key"
```

## Usage

```bash
python iplookup.py -t 8.8.8.8
```

Or run it without arguments and enter the IP when prompted:

```bash
python iplookup.py
```

### Options

| Flag | Description |
|------|-------------|
| `-t`, `--target` | IP address to look up |
| `-h`, `--help` | Show the help message |

### Example output

```
╔════════════════════════════════════════════╗
║              TARGET ACQUIRED               ║
╠════════════════════════════════════════════╣
║ IP ADDRESS : 8.8.8.8                       ║
║ COUNTRY    : United States                 ║
║ CITY       : Mountain View                 ║
║ ISP        : Google LLC                    ║
╚════════════════════════════════════════════╝
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Lookup succeeded |
| `1` | Lookup failed (bad key, rate limit, network error) |
| `130` | Interrupted with Ctrl+C |

## Notes

- The progress bars are cosmetic. The tool makes a single API request per lookup.
- The free tier has a daily request limit. If you hit it, the tool tells you when the next call frees up.
- On Windows, colors are enabled automatically in modern terminals.

## Roadmap

- [ ] `-v` verbose flag
- [ ] `--no-fx` flag to skip animations
- [ ] Domain name support
- [ ] JSON output with `-o`

## Disclaimer

This tool is for educational and legitimate network research purposes only. Only look up information you are permitted to, and follow the terms of the API provider.

## License

MIT. See `LICENSE` for details.
