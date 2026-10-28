#!/usr/bin/env python3
"""Unicode-aware search entry point shipped inside every generated skill.

The upstream lexical search (kept byte-for-byte beside this file as
``_search_index_upstream.py``) only tokenises ASCII and Chinese: accented French
words are cut at the accent and Arabic yields no token. This wrapper loads the
unmodified upstream module, replaces only its ``tokens`` function and runs the
upstream ``main``. Scoring, JSONL loading and output format stay upstream's.

Matching is accent-insensitive (``sécurité`` finds ``securite``) and Arabic
diacritics, tatweel and alef/yeh/teh-marbuta variants are normalised. There is
no stemming: ``réapprovisionner`` does not match ``réapprovisionnement``.
"""
import importlib.util
import re
import sys
import unicodedata
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_search_index_upstream", _HERE / "_search_index_upstream.py")
upstream = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(upstream)

FRENCH_STOPWORDS = {
    "au", "aux", "ce", "ces", "dans", "de", "des", "du", "elle", "en", "et", "est", "il", "je", "la", "le",
    "les", "leur", "ma", "mes", "mon", "ne", "nos", "nous", "on", "ou", "par", "pas", "pour", "que", "qui",
    "sa", "se", "ses", "son", "sur", "ta", "te", "tes", "ton", "tu", "un", "une", "vos", "vous",
}
ARABIC_STOPWORDS = {"في", "من", "على", "الى", "عن", "ان", "او", "ما", "هو", "هي", "هذا", "هذه", "التي", "الذي", "مع"}
STOPWORDS = set(upstream.ENGLISH_STOPWORDS) | FRENCH_STOPWORDS | ARABIC_STOPWORDS

_ARABIC_MARKS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_CJK = re.compile(r"[㐀-鿿]+")
_WORD = re.compile(r"\w[\w-]*")
_FOLD = str.maketrans({"ى": "ي", "ة": "ه", "œ": "oe", "æ": "ae"})


def normalize(value):
    value = unicodedata.normalize("NFKC", value).lower()
    value = _ARABIC_MARKS.sub("", value).translate(_FOLD)
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def unicode_tokens(value):
    text = normalize(str(value))
    output = set()
    for term in _CJK.findall(text):
        upstream.add_chinese_tokens(output, term)
    for raw in _WORD.findall(_CJK.sub(" ", text)):
        token = raw.strip("-_")
        if not token or token in STOPWORDS:
            continue
        if len(token) < 2 and not token.isdigit():
            continue
        output.add(token)
        # Arabic definite article: index both forms so "الأمان" and "أمان" meet.
        if token.startswith("ال") and len(token) > 4:
            output.add(token[2:])
    return output


upstream.tokens = unicode_tokens

if __name__ == "__main__":
    sys.exit(upstream.main())
