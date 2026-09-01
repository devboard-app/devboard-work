import re

MAX_MENTIONS = 20

MENTION_RE = re.compile(r'(?<![\w/])@([a-zA-Z0-9][a-zA-Z0-9_.-]{1,28}[a-zA-Z0-9])')

def extract_mentions(body: str) -> list[str]:
    found = dict.fromkeys(m.group(1).lower() for m in MENTION_RE.finditer(body))
    return list(found)[:MAX_MENTIONS]