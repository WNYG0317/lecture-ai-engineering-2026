"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_related_knowledge_matches_names_ids_and_aliases():
    glossary = tools.load_glossary()
    target = next(entry for entry in glossary if entry["id"] == "lora")
    expected = [
        entry for entry in glossary
        if entry["category"] == target["category"] and entry["id"] != target["id"]
    ][:tools.MAX_RESULTS]
    assert expected
    for query in ["LoRA", "lora", " Low-Rank Adaptation "]:
        result = json.loads(tools.related_knowledge(query))
        assert result["category"] == target["category"]
        assert [entry["id"] for entry in result["related_terms"]] == [
            entry["id"] for entry in expected
        ]
        assert [entry["definition"] for entry in result["related_terms"]] == [
            entry["definition"] for entry in expected
        ]


def test_related_knowledge_handles_empty_and_unknown_terms():
    assert "空です" in tools.related_knowledge("　 ")
    assert "見つかりませんでした" in tools.related_knowledge("存在しない用語xyz")


def test_related_knowledge_does_not_use_related_links_or_definitions(monkeypatch):
    entries = [
        {"id": "a", "term": "用語A", "aliases": [], "category": "単独", "related": ["b"]},
        {"id": "b", "term": "用語B", "aliases": [], "category": "別カテゴリ",
         "definition": "用語Aに関連する説明", "lecture": 1},
    ]
    monkeypatch.setattr(tools, "load_glossary", lambda: entries)
    assert json.loads(tools.related_knowledge("a"))["related_terms"] == []
    assert "見つかりませんでした" in tools.related_knowledge("関連する説明")


def test_related_knowledge_requests_id_for_ambiguous_alias(monkeypatch):
    entries = [
        {"id": "a", "term": "用語A", "aliases": ["共通"]},
        {"id": "b", "term": "用語B", "aliases": ["共通"]},
    ]
    monkeypatch.setattr(tools, "load_glossary", lambda: entries)
    assert "複数の用語" in tools.related_knowledge("共通")


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
