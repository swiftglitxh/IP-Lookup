#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ╔══════════════════════════════════════════════════════════════╗
# ║  Project     : IP / Domain Lookup Tool                       ║
# ║  Author      : SwiftGlitxh                                   ║
# ║  Version     : 1.2.0                                         ║
# ║  Description : Takes one or more IP addresses and returns    ║
# ║                geolocation and ISP info in a hacker-style    ║
# ║                terminal UI. Supports batch, JSON and CSV.    ║
# ╠══════════════════════════════════════════════════════════════╣
# ║  Usage       : python iplookup.py -t <ip> [options]          ║
# ║                python iplookup.py -f ips.txt -o out.csv      ║
# ║                python iplookup.py   (prompts for an IP)      ║
# ║  Flags       : -t, -i, --ip  IP address(es) to look up       ║
# ║                -f, --file    read IPs from a file            ║
# ║                -o, --output  save results (.json/.csv/.txt)  ║
# ║                -v, --verbose show extra request details      ║
# ║                -j, --json    print raw JSON                  ║
# ║                -d, --delay   seconds between batch lookups   ║
# ║                --timeout     request timeout in seconds      ║
# ║                -k, --key     API key (env is safer)          ║
# ║                --no-fx       skip the animations             ║
# ║                --no-color    disable colours                 ║
# ║                -V, --version show version                    ║
# ║  Env         : WIMI_API_KEY    your whatismyip API key       ║
# ║  Imports     : argparse, csv, ipaddress, json, os, random,   ║
# ║                sys, time                                     ║
# ║                requests (third-party)                        ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse
import csv
import ipaddress
import json
import os
import random
import sys
import time

import requests

__version__ = "1.2.0"

os.system("")  # enables ANSI colours on Windows terminals

GREEN = "\033[92m"
DARK = "\033[32m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

API_URL = "https://wimi-api.whatismyip.com/ip-address-lookup/"
PRIORITY_FIELDS = ["ip", "country", "city", "isp"]

BANNER = r"""
 ___ ____    _     ___   ___  _  ___   _ ____
|_ _|  _ \  | |   / _ \ / _ \| |/ / | | |  _ \
 | || |_) | | |  | | | | | | | ' /| | | | |_) |
 | ||  __/  | |__| |_| | |_| | . \| |_| |  __/
|___|_|     |_____\___/ \___/|_|\_\\___/|_|
"""

# Runtime switches, set from the command-line flags in main()
VERBOSE = False
QUIET = False  # True in --json mode: no banner, no chatter, only JSON on stdout
FX = True      # typing effect and progress bars


class StopBatch(Exception):
    """Raised for errors that make further lookups pointless (rate limit, bad key)."""


# ─── Output helpers ────────────────────────────────────────────

def disable_color():
    global GREEN, DARK, RED, YELLOW, CYAN, BOLD, RESET
    GREEN = DARK = RED = YELLOW = CYAN = BOLD = RESET = ""


def slow_print(text, delay=0.015, color=None, end="\n"):
    """Typewriter effect (instant when animations are off)."""
    color = GREEN if color is None else color
    if not FX:
        print(f"{color}{text}{RESET}", end=end)
        return
    sys.stdout.write(color)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RESET + end)


def say(text, color=None):
    """Normal status message. Hidden in --json mode."""
    if not QUIET:
        slow_print(text, color=color)


def err(text, color=None):
    """Errors and warnings go to stderr so they never pollute piped output."""
    color = RED if color is None else color
    print(f"{color}{text}{RESET}", file=sys.stderr)


def log(text):
    """Verbose-only debug line (stderr)."""
    if VERBOSE:
        print(f"{DARK}[v] {text}{RESET}", file=sys.stderr)


def progress(label, duration=1.2, width=30):
    """Fake-but-pretty progress bar."""
    if QUIET or not FX:
        return
    for i in range(width + 1):
        bar = "█" * i + "░" * (width - i)
        pct = int(i / width * 100)
        sys.stdout.write(f"\r{DARK}[*] {label:<22} {GREEN}[{bar}] {pct:3d}%{RESET}")
        sys.stdout.flush()
        time.sleep(duration / width + random.uniform(0, 0.02))
    print()


def show_banner():
    if QUIET:
        return
    print(f"{GREEN}{BOLD}{BANNER}{RESET}")
    print(f"{DARK}  [ author: SwiftGlitxh | v{__version__} | IP recon tool ]{RESET}\n")


# ─── Targets ───────────────────────────────────────────────────

def validate(value):
    """Return the normalised IP string, or None if it isn't a valid IP."""
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def read_target_file(path):
    """One IP per line. Blank lines and lines starting with # are ignored."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = [line.strip() for line in f]
    except OSError as e:
        err(f"[!] Could not read '{path}': {e}")
        sys.exit(1)
    return [line for line in lines if line and not line.startswith("#")]


def prompt_for_ip():
    while True:
        entry = input(f"{GREEN}root@lookup{RESET}:{CYAN}~${RESET} target > ")
        ip = validate(entry)
        if ip:
            return ip
        err("[-] Invalid IP address. Try again.")


def collect_targets(args):
    raw = list(args.target or [])
    if args.file:
        raw += read_target_file(args.file)

    if not raw:
        if QUIET:
            err("[!] --json needs a target. Use -t or -f.")
            return []
        return [prompt_for_ip()]

    targets = []
    for item in raw:
        ip = validate(item)
        if ip is None:
            err(f"[-] Skipping invalid IP: {item}")
        elif ip in targets:
            log(f"Skipping duplicate: {ip}")
        else:
            targets.append(ip)
    return targets


# ─── API ───────────────────────────────────────────────────────

def safe_json(resp):
    """Parsed JSON if it's an object, otherwise an empty dict."""
    try:
        body = resp.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def lookup(target, key, timeout):
    url = API_URL + target
    log(f"GET {url}")
    started = time.time()

    try:
        resp = requests.get(url, headers={"X-API-KEY": key}, timeout=timeout)
    except requests.Timeout:
        err(f"[!] Request timed out after {timeout:g}s for {target}")
        return None
    except requests.RequestException as e:
        err(f"[!] Network error: {e}")
        return None

    log(f"HTTP {resp.status_code} in {(time.time() - started) * 1000:.0f} ms")
    for header in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"):
        if header in resp.headers:
            log(f"{header}: {resp.headers[header]}")

    if resp.status_code == 429:
        wait = resp.headers.get("Retry-After") or safe_json(resp).get("retryAfter")
        raise StopBatch(f"[!] Daily limit reached; one call frees up in {wait or 'unknown'}")
    if resp.status_code in (401, 403):
        raise StopBatch(f"[!] API key rejected (HTTP {resp.status_code}). Check your key.")
    if not resp.ok:
        detail = safe_json(resp).get("error") or resp.text[:100]
        err(f"[!] Error {resp.status_code}: {detail}")
        return None

    data = safe_json(resp)
    if not data:
        err("[!] Response was not valid JSON.")
        return None
    return data


# ─── Display and saving ────────────────────────────────────────

def flat(value):
    """Nested values become JSON strings so they fit in a CSV cell or text line."""
    return json.dumps(value) if isinstance(value, (dict, list)) else value


def show_result(data):
    rows = [
        ("IP ADDRESS", data.get("ip")),
        ("COUNTRY", data.get("country")),
        ("CITY", data.get("city")),
        ("ISP", data.get("isp")),
    ]

    if VERBOSE:
        for k, v in data.items():
            if k not in PRIORITY_FIELDS:
                rows.append((str(k).upper(), flat(v)))

    label_w = max(len(label) for label, _ in rows)
    lines = []
    for label, value in rows:
        text = "N/A" if value in (None, "") else str(value)
        if len(text) > 60:
            text = text[:57] + "..."
        lines.append(f" {label:<{label_w}} : {text}")

    width = max(44, max(len(line) for line in lines) + 2)
    print(f"\n{GREEN}╔{'═' * width}╗")
    print(f"║{'TARGET ACQUIRED':^{width}}║")
    print(f"╠{'═' * width}╣")
    for line in lines:
        print(f"║{line:<{width}}║")
    print(f"╚{'═' * width}╝{RESET}\n")


def save_output(path, results):
    """Format is picked from the extension: .json, .csv, anything else = text."""
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "w", encoding="utf-8", newline="") as f:
            if ext == ".json":
                json.dump(results, f, indent=4)
                f.write("\n")
            elif ext == ".csv":
                extra = sorted({k for r in results for k in r} - set(PRIORITY_FIELDS))
                writer = csv.DictWriter(f, fieldnames=PRIORITY_FIELDS + extra,
                                        extrasaction="ignore")
                writer.writeheader()
                for r in results:
                    writer.writerow({k: flat(v) for k, v in r.items()})
            else:
                blocks = ["\n".join(f"{k}: {flat(v)}" for k, v in r.items()) for r in results]
                f.write("\n\n".join(blocks) + "\n")
    except OSError as e:
        err(f"[!] Could not write '{path}': {e}")
        return False

    log(f"Saved {len(results)} result(s) to {path}")
    say(f"[+] Saved results to {path}")
    return True


# ─── CLI ───────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        prog="iplookup.py",
        description="IP lookup tool (hacker style): geolocation and ISP for one or more IPs.",
        epilog=(
            "examples:\n"
            "  python iplookup.py -t 8.8.8.8\n"
            "  python iplookup.py -t 8.8.8.8 1.1.1.1 -v\n"
            "  python iplookup.py -f ips.txt -o results.csv --no-fx\n"
            "  python iplookup.py -t 8.8.8.8 --json > result.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-t", "-i", "--target", "--ip", dest="target", nargs="+",
                        metavar="IP", help="one or more IP addresses to look up")
    parser.add_argument("-f", "--file", metavar="FILE",
                        help="read IPs from FILE, one per line (# for comments)")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="save results to FILE (.json, .csv, otherwise plain text)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show extra fields and request details (URL, status, timing)")
    parser.add_argument("-j", "--json", action="store_true",
                        help="print results as raw JSON only (no banner, colours or effects)")
    parser.add_argument("-d", "--delay", type=float, default=1.0, metavar="SEC",
                        help="seconds to wait between batch lookups (default: 1.0)")
    parser.add_argument("--timeout", type=float, default=15.0, metavar="SEC",
                        help="request timeout in seconds (default: 15)")
    parser.add_argument("-k", "--key", metavar="KEY",
                        help="API key (overrides WIMI_API_KEY; env var is safer because "
                             "keys typed here stay in your shell history)")
    parser.add_argument("--no-fx", action="store_true",
                        help="skip the typing effect and progress bars")
    parser.add_argument("--no-color", action="store_true",
                        help="disable coloured output")
    parser.add_argument("-V", "--version", action="version",
                        version=f"%(prog)s {__version__}")
    return parser.parse_args()


def main():
    global VERBOSE, QUIET, FX
    args = parse_args()

    VERBOSE = args.verbose
    QUIET = args.json
    piped = not sys.stdout.isatty()
    FX = not (args.no_fx or QUIET or piped)
    if args.no_color or QUIET or piped or os.environ.get("NO_COLOR"):
        disable_color()

    show_banner()

    key = args.key or os.environ.get("WIMI_API_KEY", "")
    if not key:
        err("[!] No API key found. Set the WIMI_API_KEY environment variable "
            "(or pass -k).")
        sys.exit(1)

    targets = collect_targets(args)
    if not targets:
        err("[-] No valid targets. Nothing to do.")
        sys.exit(1)

    if len(targets) == 1:
        ip = ipaddress.ip_address(targets[0])
        say(f"[+] Valid IPv{ip.version} address: {ip}")
    else:
        say(f"[+] {len(targets)} valid targets loaded")

    progress("Initialising modules")
    progress("Tracing route")
    progress("Querying database")

    results, failed = [], 0
    for i, target in enumerate(targets, 1):
        if len(targets) > 1:
            say(f"[*] ({i}/{len(targets)}) {target}", color=DARK)
        say("[*] Decrypting response...", color=DARK)

        try:
            data = lookup(target, key, args.timeout)
        except StopBatch as e:
            err(str(e), color=YELLOW)
            failed += len(targets) - i + 1
            break

        if data is None:
            failed += 1
            say("[-] Lookup failed.", color=RED)
            continue

        results.append(data)
        say("[+] Access granted. Data received.")
        if not QUIET:
            show_result(data)

        if i < len(targets) and args.delay > 0:
            time.sleep(args.delay)

    if args.json:
        print(json.dumps(results, indent=4))

    if args.output:
        if results:
            if not save_output(args.output, results):
                failed += 1
        else:
            err("[!] No results to save.")

    if len(targets) > 1:
        say(f"[*] Done: {len(results)} succeeded, {failed} failed.", color=DARK)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        err("\n[!] Interrupted. Exiting...")
        sys.exit(130)
    except EOFError:
        err("\n[!] No input available. Use -t or -f.")
        sys.exit(1)
