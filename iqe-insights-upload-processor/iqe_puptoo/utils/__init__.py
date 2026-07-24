"""Utilities for IQE Puptoo plugin."""

from random import randint


def gen_non_ascii(size: int = 5) -> str:
    """Return a random non ascii string."""
    non_ascii_chars = ["á", "é", "í", "ó", "ú", "ç", "ã", "õ", "ñ", "à", "ü"]
    word = ""
    for _ in range(size):
        letter = non_ascii_chars[randint(0, len(non_ascii_chars) - 1)]
        word += letter
    return word
