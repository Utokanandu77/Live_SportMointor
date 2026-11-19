#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║              ⚽ GOAL ALERT - LIVE MATCH MONITOR ⚽            ║
║                    Nigeria Time (UTC+1)                      ║
╚══════════════════════════════════════════════════════════════╝
"""

import requests
import time
import os
import sys
import platform
from datetime import datetime, timezone, timedelta

# ─────────────────────────── CONFIG ────────────────────────────
NIGERIA_TZ = timezone(timedelta(hours=1))
POLL_SECONDS = 30
WIDTH = 64
DEBUG = True  # set False to hide request URLs

# ─────────────────────────── COLORS ────────────────────────────
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"

    @staticmethod
    def enable_windows():
        if platform.system() == "Windows":
            os.system("")


C.enable_windows()

# ─────────────────────────── LEAGUES ───────────────────────────
LEAGUES = {
    "1":  ("England",            "eng.1"),
    "2":  ("Spain",              "esp.1"),
    "3":  ("Italy",              "ita.1"),
    "4":  ("Germany",            "ger.1"),
    "5":  ("France",             "fra.1"),
    "6":  ("Netherlands",        "ned.1"),
    "7":  ("Portugal",           "por.1"),
    "8":  ("New Zealand",        "nzl.1"),
    "9":  ("Australia",          "aus.1"),
    "10": ("USA MLS",            "usa.1"),
    "11": ("Champions League",   "uefa.champions"),
    "12": ("Europa League",      "uefa.europa"),
    "13": ("India",              "ind.1"),
    "14": ("Brazil",             "bra.1"),
    "15": ("Argentina",          "arg.1"),
    "16": ("Mexico Liga MX",     "mex.1"),
    "17": ("Japan J1",           "jpn.1"),
    "18": ("South Korea K",      "kor.1"),
    "19": ("Saudi Pro League",   "ksa.1"),
    "20": ("Turkey Süper Lig",   "tur.1"),
    "21": ("Scotland",           "sco.1"),
    "22": ("Belgium",            "bel.1"),
}


# ─────────────────────────── UI HELPERS ────────────────────────
def border(char="═", width=WIDTH, color=C.CYAN):
    return color + char * width + C.RESET


def title_box(title, color=C.CYAN):
    pad = WIDTH - len(title) - 2
    left = pad // 2
    right = pad - left
    print(color + "╔" + "═" * (WIDTH - 2) + "╗" + C.RESET)
    print(color + "║" + " " * left + C.BOLD + title + C.RESET + color + " " * right + "║" + C.RESET)
    print(color + "╚" + "═" * (WIDTH - 2) + "╝" + C.RESET)


def line(text, color=C.RESET):
    print(color + text + C.RESET)


def clear():
    os.system("cls" if platform.system() == "Windows" else "clear")


def prompt(msg):
    return input(C.BOLD + C.YELLOW + msg + C.RESET).strip()


# ─────────────────────────── SOUND ─────────────────────────────
def play_sound():
    system = platform.system()
    try:
        if system == "Windows":
            import winsound
            for _ in range(5):
                winsound.Beep(1200, 600)
                time.sleep(0.15)
        elif system == "Darwin":
            for _ in range(3):
                os.system('say "GOAL GOAL GOAL"')
        else:
            sys.stdout.write("\a")
            sys.stdout.flush()
            for _ in range(3):
                print(C.GREEN + "🔊 BEEP BEEP BEEP - GOAL!" + C.RESET)
                time.sleep(0.3)
    except Exception as e:
        print(C.RED + f"Sound error: {e}" + C.RESET)


# ─────────────────────────── API ───────────────────────────────
def format_time(utc_str):
    try:
        dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        return dt.astimezone(NIGERIA_TZ).strftime("%I:%M %p")
    except Exception:
        return utc_str


def _request_scoreboard(league_code, date_str):
    """Raw request for one date. Returns list or None on error."""
    url = (
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/"
        f"{league_code}/scoreboard?dates={date_str}"
    )
    if DEBUG:
        print(C.DIM + f"[DEBUG] GET {url}" + C.RESET)
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("events", [])
    except requests.RequestException as e:
        if DEBUG:
            print(C.RED + f"[DEBUG] Error: {e}" + C.RESET)
        return None
    except ValueError as e:
        if DEBUG:
            print(C.RED + f"[DEBUG] Bad JSON: {e}" + C.RESET)
        return None


def fetch_events(league_code):
    """
    Try today, yesterday, tomorrow in Nigeria time.
    Returns the first non-empty list, or [] if all empty,
    or None if every request failed with a network error.
    """
    tried = []
    had_error = False
    for offset in (0, -1, 1):
        d = (datetime.now(NIGERIA_TZ) + timedelta(days=offset)).strftime("%Y%m%d")
        tried.append(d)
        events = _request_scoreboard(league_code, d)
        if events is None:
            had_error = True
            continue
        if events:
            if DEBUG and offset != 0:
                print(C.YELLOW + f"[DEBUG] Found matches on {d} (offset {offset:+d})" + C.RESET)
            return events
    if DEBUG:
        print(C.DIM + f"[DEBUG] Tried dates: {', '.join(tried)} — all empty" + C.RESET)
    return None if had_error else []


def get_home_away(comp):
    home = next((c for c in comp["competitors"] if c.get("homeAway") == "home"), None)
    away = next((c for c in comp["competitors"] if c.get("homeAway") == "away"), None)
    if not home or not away:
        home, away = comp["competitors"][0], comp["competitors"][1]
    return home, away


def extract_score(events, event_id):
    for e in events:
        if e["id"] == event_id:
            comp = e["competitions"][0]
            home, away = get_home_away(comp)
            return {
                "home": home["team"]["shortDisplayName"],
                "away": away["team"]["shortDisplayName"],
                "home_score": int(home.get("score") or 0),
                "away_score": int(away.get("score") or 0),
                "status": e["status"]["type"]["description"],
                "state": e["status"]["type"].get("state", ""),
                "clock": e["status"].get("displayClock", ""),
            }
    return None


# ─────────────────────────── SCREENS ───────────────────────────
def screen_country():
    clear()
    title_box("⚽  GOAL ALERT  ⚽  Pick a Country")
    print()
    keys = list(LEAGUES.keys())
    half = (len(keys) + 1) // 2
    for i in range(half):
        left = keys[i]
        lname = LEAGUES[left][0]
        lstr = f"{C.BOLD}{C.YELLOW}{left:>2}{C.RESET}. {lname}"
        lstr = lstr + " " * max(0, 32 - len(lname) - len(left))
        if i + half < len(keys):
            right = keys[i + half]
            rname = LEAGUES[right][0]
            rstr = f"{C.BOLD}{C.YELLOW}{right:>2}{C.RESET}. {rname}"
            print(lstr + rstr)
        else:
            print(lstr)
    print()
    return prompt("➤  Type country number: ")


def screen_matches(country_name, events):
    clear()
    title_box(f"📅  Today's Matches — {country_name} (Nigeria Time)", color=C.GREEN)
    print()
    for i, game in enumerate(events, start=1):
        comp = game["competitions"][0]
        home, away = get_home_away(comp)
        hn = home["team"]["shortDisplayName"]
        an = away["team"]["shortDisplayName"]
        start = format_time(game["date"])
        status = game["status"]["type"]["description"]
        state = game["status"]["type"].get("state", "")
        color = C.GREEN if state == "in" else (C.DIM if state == "post" else C.CYAN)
        marker = "🔴 LIVE" if state == "in" else ("✅ FIN" if state == "post" else "🕐 SCH")
        print(
            f"{C.BOLD}{C.YELLOW}{i:>2}{C.RESET}. "
            f"{color}{hn:<18}{C.RESET} vs {color}{an:<18}{C.RESET} "
            f" {C.DIM}{start}{C.RESET}  {marker}  {C.DIM}{status}{C.RESET}"
        )
    print()
    return prompt("➤  Which match to monitor? (number): ")


def screen_monitor_header(home, away):
    clear()
    title_box("🔴  LIVE MATCH MONITOR", color=C.RED)
    print()
    print(C.BOLD + C.WHITE + f"   {home}  vs  {away}".center(WIDTH) + C.RESET)
    print(C.DIM + f"   Polling every {POLL_SECONDS}s · Ctrl+C to stop".center(WIDTH) + C.RESET)
    print()
    print(border("─", WIDTH, C.DIM))


# ─────────────────────────── MAIN ──────────────────────────────
def main():
    try:
        # ── country ──
        choice = screen_country()
        if choice not in LEAGUES:
            print(C.RED + "Invalid choice." + C.RESET)
            return
        country_name, league_code = LEAGUES[choice]

        # ── fetch ──
        line(f"\n{C.DIM}Fetching matches for {country_name}...{C.RESET}")
        events = fetch_events(league_code)
        if events is None:
            print(C.RED + "\n⚠️  Could not reach ESPN. Check your connection." + C.RESET)
            return
        if not events:
            print(C.YELLOW + f"\nNo matches found for {country_name} "
                             f"(tried today, yesterday, tomorrow)." + C.RESET)
            return

        # ── pick match ──
        pick = screen_matches(country_name, events)
        try:
            idx = int(pick) - 1
            if idx < 0 or idx >= len(events):
                raise ValueError
            selected = events[idx]
        except ValueError:
            print(C.RED + "Invalid number." + C.RESET)
            return

        event_id = selected["id"]
        comp = selected["competitions"][0]
        home, away = get_home_away(comp)
        home_team = home["team"]["shortDisplayName"]
        away_team = away["team"]["shortDisplayName"]

        # ── monitor ──
        screen_monitor_header(home_team, away_team)

        last_score = None
        last_status = None
        goal_count = 0

        while True:
            events = fetch_events(league_code)
            if events is None:
                time.sleep(POLL_SECONDS)
                continue

            info = extract_score(events, event_id)
            if info is None:
                print(C.YELLOW + "\n⚠️  Match left the feed. Stopping." + C.RESET)
                break

            current = (info["home_score"], info["away_score"])
            now = datetime.now(NIGERIA_TZ).strftime("%I:%M:%S %p")

            if last_score is not None and current != last_score:
                goal_count += 1
                print()
                print(border("═", WIDTH, C.GREEN))
                print(C.BOLD + C.BG_GREEN + C.WHITE + "  ⚽  G O A L !!!  ⚽  ".center(WIDTH) + C.RESET)
                print(border("═", WIDTH, C.GREEN))
                print(
                    C.BOLD + C.WHITE
                    + f"   {info['home']}  {info['home_score']} - {info['away_score']}  {info['away']}".center(WIDTH)
                    + C.RESET
                )
                print(C.DIM + f"   {now} · Goal #{goal_count}".center(WIDTH) + C.RESET)
                print(border("═", WIDTH, C.GREEN))
                play_sound()

            if info["status"] != last_status:
                print(C.MAGENTA + f"📢  {info['status']}" + C.RESET)
                last_status = info["status"]

            clock = f" {info['clock']}" if info["clock"] else ""
            print(
                C.DIM + f"[{now}] " + C.RESET
                + C.BOLD + C.WHITE
                + f"{info['home']} {C.GREEN}{info['home_score']}{C.WHITE} - "
                + f"{C.GREEN}{info['away_score']}{C.WHITE} {info['away']}"
                + C.RESET
                + C.DIM + f"{clock}  |  {info['status']}" + C.RESET
            )

            last_score = current

            if info["state"] == "post":
                print()
                print(border("─", WIDTH, C.CYAN))
                print(C.BOLD + C.CYAN + "🏁  MATCH FINISHED".center(WIDTH) + C.RESET)
                print(border("─", WIDTH, C.CYAN))
                break

            time.sleep(POLL_SECONDS)

    except KeyboardInterrupt:
        print(C.YELLOW + "\n\n👋 Monitoring stopped." + C.RESET)
    except Exception as e:
        print(C.RED + f"\n❌ Unexpected error: {e}" + C.RESET)


if __name__ == "__main__":
    main()