# OvFlashcards

A personal language learning flashcard app for macOS, built with Python and PySide6.

---

## Features

- **Multiple language decks** — create a separate deck for each language you are learning
- **Flashcards** — each card has a word, translation, description, and a colour
- **14 card colours** — visually organise your cards by topic or category
- **Show all cards** — browse all cards in a scrollable grid, sorted by colour
- **Search** — live search across words and translations
- **Spaced repetition practice** — review cards on a schedule based on how well you know them
  - Due cards (past or present) are shown first, sorted by most overdue
  - New cards are shown after due cards
  - Rate each card as **Hard** (+1 day), **Medium** (+3 days), or **Easy** (+7 days)
- **Edit and delete** cards at any time
- **Delete entire decks** when you no longer need them

---

## Requirements

- macOS
- Python 3.11+
- [Homebrew](https://brew.sh)
- [pyenv](https://github.com/pyenv/pyenv)

---

## Installation

### 1. Clone the repository

```bash
git clone git@github.com:OvaisQazi/OvFlashcards.git
cd OvFlashcards
```

### 2. Set up Python environment

```bash
pyenv install 3.14
pyenv local 3.14
python -m venv env
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python main.py
```

---

## Project Structure

```
OvFlashcards/
├── main.py                  # Entry point
├── database.py              # All SQLite operations
├── scheduler.py             # Spaced repetition interval constants
├── requirements.txt
│
└── ui/
    ├── styles.py            # Theme, colours, button styles
    ├── app_window.py        # Main window and navigation stack
    ├── start_screen.py      # Landing page — pick or create a deck
    ├── home_screen.py       # Per-language home screen
    ├── add_card_dialog.py   # Add / Edit card form
    ├── search_screen.py     # Live search
    ├── all_cards_screen.py  # Grid view of all cards
    ├── card_view_screen.py  # Single card view with flip animation
    ├── marquee_label.py     # Scrolling text widget for long words
    └── practice_screen.py  # Spaced repetition practice session
```

---

## Data Storage

User data (language decks and cards) is stored locally at:

```
~/OvFlashcards/data/
```

Each language gets its own SQLite database file (e.g. `german.db`). No data is sent anywhere — everything stays on your machine.

---

## Tech Stack

| | |
|---|---|
| Language | Python 3.14 |
| GUI | PySide6 (Qt6) |
| Database | SQLite3 (built-in) |
| Packaging | PyInstaller |

---

## License

MIT License — see [LICENSE](LICENSE) for details.