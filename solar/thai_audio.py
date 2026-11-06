"""Recordings of the Thai phrases, made once with a neural Thai voice and kept on the data branch.

    python -m solar.thai_audio --check   # exit 1 if any recording is missing
    python -m solar.thai_audio           # make the missing ones (needs `pip install edge-tts`)
"""
import asyncio
import hashlib
import os
import sys
from pathlib import Path

VOICE = "th-TH-PremwadeeNeural"
SLOW = "-35%"


def name(thai, slow=False):
    """File name for a phrase. It follows the Thai text, so editing a phrase makes a new recording."""
    return hashlib.sha1(thai.encode("utf-8")).hexdigest()[:12] + ("-slow" if slow else "") + ".mp3"


def missing(folder):
    from .daily import THAI_PHRASES
    return [(t, slow) for t, *_ in THAI_PHRASES for slow in (False, True) if not (folder / name(t, slow)).exists()]


async def make(folder, todo):
    import edge_tts
    folder.mkdir(parents=True, exist_ok=True)
    for thai, slow in todo:
        out = folder / name(thai, slow)
        try:
            await edge_tts.Communicate(thai, VOICE, rate=SLOW if slow else "+0%").save(str(out) + ".part")
            os.replace(str(out) + ".part", out)
            print("Recorded", out.name)
        except Exception as e:  # one failed phrase shouldn't stop the rest; it is tried again next run
            print("Could not record", thai, e, file=sys.stderr)


def main():
    folder = Path(os.environ.get("DATA_DIR", "data")) / "thai"
    todo = missing(folder)
    if "--check" in sys.argv:
        sys.exit(1 if todo else 0)
    if todo:
        asyncio.run(make(folder, todo))


if __name__ == "__main__":
    main()
