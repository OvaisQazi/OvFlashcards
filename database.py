import sqlite3
import os

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
    """Create a new SQLite database file for the given language."""
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
            color       TEXT DEFAULT '#FFF8E7',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
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
    return [{"id": r[0], "word": r[1], "translation": r[2], "description": r[3], "color": r[4]} for r in rows]


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
    return [{"id": r[0], "word": r[1], "translation": r[2], "description": r[3], "color": r[4]} for r in rows]