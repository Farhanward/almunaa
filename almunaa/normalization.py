from __future__ import annotations

import base64
import binascii
import html
import re
import unicodedata
from urllib.parse import unquote


ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)
BASE64_TOKEN = re.compile(r"\b[A-Za-z0-9+/_-]{16,}={0,2}\b")
CONFUSABLES = str.maketrans(
    {
        "Α": "A",
        "А": "A",
        "Ɑ": "A",
        "Β": "B",
        "С": "C",
        "Ϲ": "C",
        "Ε": "E",
        "Е": "E",
        "Η": "H",
        "Ι": "I",
        "І": "I",
        "Ο": "O",
        "О": "O",
        "Ρ": "P",
        "Р": "P",
        "Τ": "T",
        "Т": "T",
        "Χ": "X",
        "Х": "X",
        "Υ": "Y",
        "У": "Y",
        "а": "a",
        "ɑ": "a",
        "α": "a",
        "с": "c",
        "ϲ": "c",
        "е": "e",
        "ε": "e",
        "і": "i",
        "ι": "i",
        "ο": "o",
        "о": "o",
        "р": "p",
        "ѕ": "s",
        "т": "t",
        "χ": "x",
        "у": "y",
        "€": "e",
        "@": "a",
        "$": "s",
        "+": "t",
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "!": "i",
        "|": "l",
    }
)


def normalize_text(text: str) -> str:
    value = html.unescape(text or "")
    value = unquote(value)
    value = value.translate(ZERO_WIDTH)
    value = re.sub(r"[\u202a-\u202e\u2066-\u2069]", "", value)
    return value


def deobfuscate_text(text: str) -> str:
    value = normalize_text(text)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = value.translate(CONFUSABLES)
    value = re.sub(r"<\s*split\s*>", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value


def _mostly_printable(value: str) -> bool:
    if not value:
        return False
    printable = sum(1 for char in value if char.isprintable() or char in "\r\n\t")
    return printable / max(1, len(value)) >= 0.85


def _decode_base64_token(token: str) -> list[str]:
    padded = token + ("=" * ((4 - len(token) % 4) % 4))
    outputs: list[str] = []
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            raw = decoder(padded.encode("ascii"))
        except (binascii.Error, ValueError):
            continue
        for encoding in ("utf-8", "utf-16le"):
            try:
                decoded = raw.decode(encoding).strip("\x00\r\n\t ")
            except UnicodeDecodeError:
                continue
            if 4 <= len(decoded) <= 5000 and _mostly_printable(decoded):
                outputs.append(decoded)
    return outputs


def text_variants(text: str, max_decoded_tokens: int = 12) -> list[tuple[str, str]]:
    original = text or ""
    normalized = normalize_text(original)
    deobfuscated = deobfuscate_text(original)
    squashed = re.sub(r"[^a-z0-9\u0600-\u06ff]+", "", deobfuscated)
    variants = [("original", original)]
    if normalized != original:
        variants.append(("normalized", normalized))
    if deobfuscated not in {original, normalized}:
        variants.append(("deobfuscated", deobfuscated))
    if 8 <= len(squashed) <= 5000 and squashed not in {original, normalized, deobfuscated}:
        variants.append(("squashed", squashed))

    seen = {original, normalized, deobfuscated, squashed}
    decoded_count = 0
    for match in BASE64_TOKEN.finditer(normalized):
        if decoded_count >= max_decoded_tokens:
            break
        for decoded in _decode_base64_token(match.group(0)):
            if decoded in seen:
                continue
            seen.add(decoded)
            decoded_count += 1
            variants.append(("decoded_base64", decoded))
            if decoded_count >= max_decoded_tokens:
                break
    return variants
