import sqlite3
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def get_db_path(language):
    return os.path.join(DATA_DIR, f"{language.lower()}.db")


def get_all_languages():
    ensure_data_dir()
    languages = []
    for f in sorted(os.listdir(DATA_DIR)):
        if f.endswith(".db"):
            languages.append(f[:-3].capitalize())
    return languages


def language_exists(language):
    return os.path.exists(get_db_path(language))


def create_language_db(language):
    ensure_data_dir()
    path = get_db_path(language)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            word        TEXT NOT NULL,
            translation TEXT NOT NULL,
            description TEXT DEFAULT '',
            color       TEXT DEFAULT '#FFE4E1',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due         TIMESTAMP,
            stability   REAL,
            difficulty  REAL,
            state       INTEGER DEFAULT 0,
            step        INTEGER DEFAULT 0,
            last_review TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def migrate_cards_table(language):
    """Add FSRS columns to existing DBs that predate spaced repetition."""
    path = get_db_path(language)
    if not os.path.exists(path):
        return
    conn = sqlite3.connect(path)
    c = conn.cursor()
    existing = {row[1] for row in c.execute("PRAGMA table_info(cards)")}
    new_cols = {
        "due":         "TIMESTAMP",
        "stability":   "REAL",
        "difficulty":  "REAL",
        "state":       "INTEGER DEFAULT 0",
        "step":        "INTEGER DEFAULT 0",
        "last_review": "TIMESTAMP",
    }
    for col, col_type in new_cols.items():
        if col not in existing:
            c.execute(f"ALTER TABLE cards ADD COLUMN {col} {col_type}")
    conn.commit()
    conn.close()


def get_all_cards(language):
    path = get_db_path(language)
    if not os.path.exists(path):
        return []
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("SELECT id, word, translation, description, color FROM cards ORDER BY word ASC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "word": r[1], "translation": r[2],
             "description": r[3], "color": r[4]} for r in rows]


def get_due_cards(language):
    """
    Returns cards due now. If nothing is due, returns all cards ordered
    by due date (soonest first) so practice always has something to show.
    """
    migrate_cards_table(language)
    path = get_db_path(language)
    if not os.path.exists(path):
        return []
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(path)
    c = conn.cursor()

    # First try: new cards + overdue cards
    c.execute("""
        SELECT id, word, translation, description, color,
               due, stability, difficulty, state, step, last_review
        FROM cards
        WHERE state = 0 OR (state > 0 AND (due IS NULL OR due <= ?))
        ORDER BY CASE WHEN state = 0 THEN 1 ELSE 0 END, due ASC
    """, (now,))
    rows = c.fetchall()

    # Fallback: if nothing is due, return all cards sorted by due date
    if not rows:
        c.execute("""
            SELECT id, word, translation, description, color,
                   due, stability, difficulty, state, step, last_review
            FROM cards
            ORDER BY due ASC NULLS FIRST
        """)
        rows = c.fetchall()

    conn.close()
    return [_row_to_card(r) for r in rows]


def save_card_review(language, card_id, fsrs_card):
    """Persist the updated FSRS state after a review."""
    path = get_db_path(language)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    due         = fsrs_card.due.isoformat()         if fsrs_card.due         else None
    last_review = fsrs_card.last_review.isoformat() if fsrs_card.last_review else None
    state       = int(fsrs_card.state)              if fsrs_card.state       else 0
    c.execute("""
        UPDATE cards SET
            due         = ?,
            stability   = ?,
            difficulty  = ?,
            state       = ?,
            step        = ?,
            last_review = ?
        WHERE id = ?
    """, (
        due,
        fsrs_card.stability,
        fsrs_card.difficulty,
        state,
        fsrs_card.step,
        last_review,
        card_id,
    ))
    conn.commit()
    conn.close()


def _row_to_card(r):
    return {
        "id": r[0], "word": r[1], "translation": r[2],
        "description": r[3], "color": r[4],
        "due": r[5], "stability": r[6], "difficulty": r[7],
        "state": r[8], "step": r[9], "last_review": r[10],
    }


def add_card(language, word, translation, description, color):
    path = get_db_path(language)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO cards (word, translation, description, color) VALUES (?, ?, ?, ?)",
        (word, translation, description, color)
    )
    conn.commit()
    conn.close()


def update_card(language, card_id, word, translation, description, color):
    path = get_db_path(language)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        "UPDATE cards SET word=?, translation=?, description=?, color=? WHERE id=?",
        (word, translation, description, color, card_id)
    )
    conn.commit()
    conn.close()


def delete_card(language, card_id):
    path = get_db_path(language)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("DELETE FROM cards WHERE id=?", (card_id,))
    conn.commit()
    conn.close()


def delete_language_db(language):
    path = get_db_path(language)
    if os.path.exists(path):
        os.remove(path)


def search_cards(language, query):
    path = get_db_path(language)
    if not os.path.exists(path):
        return []
    conn = sqlite3.connect(path)
    c = conn.cursor()
    q = f"%{query}%"
    c.execute(
        "SELECT id, word, translation, description, color FROM cards "
        "WHERE word LIKE ? OR translation LIKE ? ORDER BY word ASC",
        (q, q)
    )
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "word": r[1], "translation": r[2],
             "description": r[3], "color": r[4]} for r in rows]