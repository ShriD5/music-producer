# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Sonic identity ledger: what every past film sounded like, so the next one is different on purpose.

  uv run ledger.py show [--n 8]
  uv run ledger.py add --project acme-launch --genre "..." --bpm 120 --key "F minor" --palette "..." --signature "..." \
                       --music-source "eleven plan" [--notes "..."]
"""
import argparse
import json
import pathlib
import time

import os

# per user, not per skill install: survives updates and stays out of the repo
LEDGER = pathlib.Path(os.environ.get("MUSIC_PRODUCER_LEDGER", "~/.config/music-producer/ledger.jsonl")).expanduser()
if not LEDGER.exists() and pathlib.Path("~/.config/sound-design/ledger.jsonl").expanduser().exists():  # pre-rename
    LEDGER = pathlib.Path("~/.config/sound-design/ledger.jsonl").expanduser()


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("show")
    s.add_argument("--n", type=int, default=8)
    a_ = sp.add_parser("add")
    for f in ("project", "genre", "key", "palette", "signature", "music-source", "notes"):
        a_.add_argument(f"--{f}", default="")
    a_.add_argument("--bpm", type=float)
    a = ap.parse_args()
    if a.cmd == "add":
        row = {"date": time.strftime("%Y-%m-%d"), "project": a.project, "genre": a.genre, "bpm": a.bpm, "key": a.key,
               "palette": a.palette, "signature": a.signature, "music_source": a.music_source, "notes": a.notes}
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
        print("logged", row["project"])
        return
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()] if LEDGER.exists() else []
    rows.sort(key=lambda r: r.get("date", ""))  # "the last 3" = the 3 most recent films
    if not rows:
        print("ledger empty")
    for r in rows[-a.n:]:
        print(f"{r['date']}  {r['project']:<18} {r.get('bpm') or '-':>5} bpm  {r.get('key', ''):<9} {r['genre']}\n"
              f"{'':12}palette: {r.get('palette', '')}\n{'':12}signature: {r.get('signature', '')}")
    print("\nThe next film must differ from the last 3 on at least three of: genre, tempo band (+-15 bpm), "
          "key/mode, lead instrument, signature sound.")


if __name__ == "__main__":
    main()
