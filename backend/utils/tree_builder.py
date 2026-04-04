import re

def build_tree(paths: list[str]) -> dict:
    tree = {}
    for path in paths:
        parts = path.replace("\\\\", "/").split("/")
        cur = tree
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = None
    return tree


def _quick_summary(docs) -> str:
    if not docs:
        return "No content found."
    text  = re.sub(r"<[^>]+>", " ", " ".join(d.page_content for d in docs))
    lines = [l.strip() for l in text.split("\\n") if l.strip()]
    s     = " ".join(lines[:3])
    return (s[:197] + "...") if len(s) > 200 else s or "No readable text."
