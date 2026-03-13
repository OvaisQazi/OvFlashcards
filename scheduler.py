"""
Thin wrapper around the `fsrs` library (Scheduler API).
"""

from datetime import datetime, timezone
from fsrs import Scheduler, Card, Rating, State       # noqa: F401  (re-export Rating)

_scheduler = Scheduler()


def _db_card_to_fsrs(db_card: dict) -> Card:
    """Convert a database card dict into an fsrs Card object."""
    card = Card()

    if db_card.get("state"):
        card.stability  = db_card.get("stability")
        card.difficulty = db_card.get("difficulty")
        card.step       = db_card.get("step") or 0

        try:
            card.state = State(db_card["state"])
        except Exception:
            pass

        if db_card.get("due"):
            try:
                card.due = datetime.fromisoformat(db_card["due"])
                if card.due.tzinfo is None:
                    card.due = card.due.replace(tzinfo=timezone.utc)
            except ValueError:
                card.due = datetime.now(timezone.utc)

        if db_card.get("last_review"):
            try:
                card.last_review = datetime.fromisoformat(db_card["last_review"])
                if card.last_review.tzinfo is None:
                    card.last_review = card.last_review.replace(tzinfo=timezone.utc)
            except ValueError:
                card.last_review = None

    return card


def rate_card(db_card: dict, rating: Rating) -> Card:
    """
    Apply a rating to a card and return the updated fsrs Card.
    Call database.save_card_review() afterwards to persist.
    """
    fsrs_card = _db_card_to_fsrs(db_card)
    now = datetime.now(timezone.utc)
    updated_card, _ = _scheduler.review_card(fsrs_card, rating, now)
    return updated_card


def days_until_due(db_card: dict) -> int:
    """How many days until this card is due (0 = due now / overdue)."""
    if not db_card.get("due"):
        return 0
    try:
        due = datetime.fromisoformat(db_card["due"])
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        delta = (due - datetime.now(timezone.utc)).days
        return max(0, delta)
    except ValueError:
        return 0