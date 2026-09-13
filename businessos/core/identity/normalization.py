def normalize_email_identity(email: str) -> str:
    """Return the canonical, case-insensitive BusinessOS login identity."""
    return email.strip().lower()
