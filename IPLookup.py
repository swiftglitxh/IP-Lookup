#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ╔══════════════════════════════════════════════════════════════╗
# ║  Project     : IP / Domain Lookup Tool                       ║
# ║  Author      : SwiftGlitxh                                   ║
# ║  Version     : 1.1.0                                         ║
# ║  Description : Takes an IP address and returns geolocation   ║
# ║                and ISP info in a hacker-style terminal UI.   ║
# ╠══════════════════════════════════════════════════════════════╣
# ║  Usage       : python iplookup.py -t <ip>                    ║
# ║                python iplookup.py   (prompts for an IP)      ║
# ║  Flags       : -t / --target   IP address to look up         ║
# ║  Env         : WIMI_API_KEY    your whatismyip API key       ║
# ║  Imports     : argparse, ipaddress, os, random, sys, time    ║
# ║                requests (third-party)                        ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse
import ipaddress
import os
import random
import sys
import time

import requests

os.system("")  # enables ANSI colours on Windows terminals

GREEN = "\033[92m"
DARK = "\033[32m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

API_URL = "https://wimi-api.whatismyip.com/ip-address-lookup/"
API_KEY = os.environ.get("WIMI_API_KEY", "")

BANNER = r"""
 ___ ____    _     ___   ___  _  ___   _ ____
|_ _|  _ \  | |   / _ \ / _ \| |/ / | | |  _ \
 | || |_) | | |  | | | | | | | ' /| | | | |_) |
 | ||  __/  | |__| |_| | |_| | . \| |_| |  __/
|___|_|     |_____\___/ \___/|_|\_\\___/|_|
"""


def slow_print(text, delay=0.015, color=GREEN, end="\n"):
    """Typewriter effect."""
    sys.stdout.write(color)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RESET + end)


def progress(label, duration=1.2, width=30):
    """Fake-but-pretty progress bar."""
    steps = width
    for i in range(steps + 1):
        bar = "█" * i + "░" * (steps - i)
        pct = int(i / steps * 100)
        sys.stdout.write(f"\r{DARK}[*] {label:<22} {GREEN}[{bar}] {pct:3d}%{RESET}")
        sys.stdout.flush()
        time.sleep(duration / steps + random.uniform(0, 0.02))
    print()


def show_banner():
    print(f"{GREEN}{BOLD}{BANNER}{RESET}")
    print(f"{DARK}  [ author: SwiftGlitxh | v1.1.0 | IP recon tool ]{RESET}\n")


def get_target(arg):
    """Use -t if given, otherwise prompt until a valid IP is entered."""
    while True:
        target = (arg or input(f"{GREEN}root@lookup{RESET}:{CYAN}~${RESET} target > ")).strip()
        try:
            ip = ipaddress.ip_address(target)
            slow_print(f"[+] Valid IPv{ip.version} address: {ip}")
            return str(ip)
        except ValueError:
            print(f"{RED}[-] Invalid IP address. Try again.{RESET}")
            arg = None  # fall back to prompting


def lookup(target):
    if not API_KEY:
        print(f"{RED}[!] No API key found. Set the WIMI_API_KEY environment variable.{RESET}")
        return None

    try:
        resp = requests.get(API_URL + target, headers={"X-API-KEY": API_KEY}, timeout=15)
    except requests.RequestException as e:
        print(f"{RED}[!] Network error: {e}{RESET}")
        return None

    if resp.status_code == 429:
        wait = resp.headers.get("Retry-After") or resp.json().get("retryAfter")
        print(f"{YELLOW}[!] Daily limit reached; one call frees up in {wait}{RESET}")
        return None
    if not resp.ok:
        try:
            err = resp.json().get("error")
        except ValueError:
            err = resp.text[:100]
        print(f"{RED}[!] Error {resp.status_code}: {err}{RESET}")
        return None

    return resp.json()


def show_result(data):
    rows = [
        ("IP ADDRESS", data.get("ip")),
        ("COUNTRY", data.get("country")),
        ("CITY", data.get("city")),
        ("ISP", data.get("isp")),
    ]
    width = 44
    print(f"\n{GREEN}╔{'═' * width}╗")
    print(f"║{'TARGET ACQUIRED':^{width}}║")
    print(f"╠{'═' * width}╣")
    for label, value in rows:
        line = f" {label:<11}: {value or 'N/A'}"
        print(f"║{line:<{width}}║")
    print(f"╚{'═' * width}╝{RESET}\n")


def parse_args():
    parser = argparse.ArgumentParser(description="IP lookup tool (hacker style).")
    parser.add_argument("-t", "--target", help="IP address to look up")
    return parser.parse_args()


def main():
    args = parse_args()
    show_banner()

    target = get_target(args.target)

    progress("Initialising modules")
    progress("Tracing route")
    progress("Querying database")

    slow_print("[*] Decrypting response...", color=DARK)
    data = lookup(target)
    if data is None:
        slow_print("[-] Lookup failed. Aborting.", color=RED)
        sys.exit(1)

    slow_print("[+] Access granted. Data received.")
    show_result(data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}[!] Interrupted. Exiting...{RESET}")
        sys.exit(130)
