# clonehero-score-exporter
Extracts scores and song information from Clone Hero's `scoredata.bin`, `scoresext.bin` and `songcache.bin` into JSON and CSV, and prints your total plays and playtime to the terminal.

# Requirements
Python 3.6+

# Setup
Open `main.py` and set `DEFAULT_CH_DIR` to your Clone Hero data folder. 

On Windows this is usually:
`C:\Users\<username>\AppData\LocalLow\srylain Inc_\Clone Hero`

# Usage
Save & run `main.py`

The script writes two files to the directory you run it from (overwriting any previous copies) and prints totals to the console:

- **scores.json** — everything parsed, keyed by chart checksum, including songs that are no longer in your library.
- **scores.csv** — one row per song/instrument with general metadata, instrument, difficulty, %, stars, score, plays, time played, avg duration
- Total plays and total playtime printed to the terminal output

# Notes
- Time played and avg duration are `h:mm:ss`. They're blank when the game didn't record playtime (older versions?). Avg duration is approximate, since restarts and quits seem to count as plays.
- Song names are cleaned of formatting tags for readability
