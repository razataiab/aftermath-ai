from typing import List
from urllib.parse import parse_qs

def parse_slash_payload(body: bytes):
    body_str = body.decode("utf-8")
    parsed = parse_qs(body_str)
    return {k: v[0] if v else "" for k, v in parsed.items()}