"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def related_knowledge(term: str) -> str:
    """用語集のカテゴリを使い、同じカテゴリの関連用語と説明を最大3件返す。

    ユーザーが用語の意味を聞いたとき、search_glossary と併せて使い、
    関連して学ぶとよい用語を提案する。term には用語名・ID・別名のいずれかを
    1つ指定する（例: "LoRA"）。意味検索は行わず、対象用語自身は候補から除く。
    """
    query = _normalize(term)
    if not query:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()
    matches = [entry for entry in glossary if query in _names(entry)]
    if not matches:
        return f"用語集に「{term}」は見つかりませんでした。用語名・ID・別名を指定してください。"
    if len(matches) > 1:
        return "複数の用語に一致しました。用語のIDを指定してください: " + ", ".join(
            entry["id"] for entry in matches
        )
    target = matches[0]
    candidates = [
        entry for entry in glossary
        if entry["id"] != target["id"] and entry["category"] == target["category"]
    ][:MAX_RESULTS]
    return json.dumps(
        {
            "term": target["term"],
            "category": target["category"],
            "related_terms": [
                {
                    "id": entry["id"],
                    "term": entry["term"],
                    "lecture": entry["lecture"],
                    "definition": entry["definition"],
                }
                for entry in candidates
            ],
        },
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")
