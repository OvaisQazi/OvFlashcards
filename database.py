import sqlite3
import os
from datetime import date, datetime

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
            next_review DATE DEFAULT NULL,
            review_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


def migrate_cards_table(language):
    """Add practice columns to older DBs."""
    path = get_db_path(language)
    if not os.path.exists(path):
        return
    conn = sqlite3.connect(path)
    c = conn.cursor()
    existing = {row[1] for row in c.execute("PRAGMA table_info(cards)")}
    if "next_review" not in existing:
        c.execute("ALTER TABLE cards ADD COLUMN next_review DATE DEFAULT NULL")
    if "review_count" not in existing:
        c.execute("ALTER TABLE cards ADD COLUMN review_count INTEGER DEFAULT 0")
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


def get_practice_cards(language):
    """
    Returns (due_cards, new_cards) as two separate lists.

    due_cards  — cards whose next_review is today or in the past,
                 sorted by next_review ascending (most overdue first).
    new_cards  — cards never practiced (next_review IS NULL),
                 in insertion order.
    """
    migrate_cards_table(language)
    path = get_db_path(language)
    if not os.path.exists(path):
        return [], []

    today = date.today().isoformat()
    conn = sqlite3.connect(path)
    c = conn.cursor()

    # Due cards: next_review <= today
    c.execute("""
        SELECT id, word, translation, description, color, next_review, review_count
        FROM cards
        WHERE next_review IS NOT NULL AND next_review <= ?
        ORDER BY next_review ASC
    """, (today,))
    due_rows = c.fetchall()

    # New cards: never reviewed
    c.execute("""
        SELECT id, word, translation, description, color, next_review, review_count
        FROM cards
        WHERE next_review IS NULL
        ORDER BY id ASC
    """)
    new_rows = c.fetchall()

    conn.close()

    def to_card(r):
        return {"id": r[0], "word": r[1], "translation": r[2],
                "description": r[3], "color": r[4],
                "next_review": r[5], "review_count": r[6]}

    return [to_card(r) for r in due_rows], [to_card(r) for r in new_rows]


def save_review(language, card_id, days_until_next: int):
    """
    Set next_review to today + days_until_next and increment review_count.
    """
    from datetime import timedelta
    next_date = (date.today() + timedelta(days=days_until_next)).isoformat()
    path = get_db_path(language)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""
        UPDATE cards
        SET next_review  = ?,
            review_count = review_count + 1
        WHERE id = ?
    """, (next_date, card_id))
    conn.commit()
    conn.close()


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