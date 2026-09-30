"""Plumbing tests with the fake backend (no model needed): python -m unittest discover tests

These check the harness logic only. They say nothing about answer quality; the
evidence in evidence/offline/ comes from real local Gemma runs.
"""
import os
import sys
import unittest
from pathlib import Path

os.environ["WIKI_BACKEND"] = "fake"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.config import load_config  # noqa: E402
from harness.ingest import build_catalog, load_plan  # noqa: E402
from harness.llm import make_client  # noqa: E402
from harness.modes import ChatSession, ask, check_citations  # noqa: E402
from harness.retrieval import Index, build_index, split_sections, tokenize  # noqa: E402


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config()
        cls.catalog = build_catalog(cls.cfg, Path(cls.cfg["raw_dir"]).resolve() if Path(cls.cfg["raw_dir"]).is_absolute()
                                    else Path(__file__).resolve().parent.parent / cls.cfg["raw_dir"], load_plan(cls.cfg))
        cls.index = Index(build_index(cls.cfg, cls.catalog))
        cls.client = make_client(cls.cfg)

    def test_three_originals_catalogued(self):
        self.assertGreaterEqual(len(self.catalog), 3)
        self.assertTrue(all(len(c["sha256"]) == 64 for c in self.catalog))

    def test_code_fence_headings_ignored(self):
        secs = split_sections("# A\ntext\n```\n# not a heading\n```\n## B\nmore")
        self.assertEqual([s[0] for s in secs], ["A", "A > B"])

    def test_stemming_matches_paraphrase(self):
        self.assertEqual(tokenize("moved")[0], tokenize("Move")[0])

    def test_search_returns_paths_and_lines(self):
        r = self.index.search("exploration rate", k=3)[0]
        self.assertIn("vault/raw/", r["path"])
        self.assertLessEqual(r["line_start"], r["line_end"])

    def test_ask_has_no_history_and_cites(self):
        rec = ask(self.cfg, self.client, self.index, "What mean evaluation score did the Pac-Man agent reach?")
        self.assertTrue(rec["citations"])
        self.assertNotIn("history", rec)

    def test_unmatched_question_is_insufficient_without_model(self):
        rec = ask(self.cfg, self.client, self.index, "zzz-unknowable quux")
        self.assertFalse(rec["model_called"])
        self.assertIn("INSUFFICIENT EVIDENCE", rec["answer"])

    def test_citation_check_flags_bad_label_and_number(self):
        passages = [{"text": "score was 876.0", "path": "x", "section": "s", "line_start": 1, "line_end": 1}]
        _, chk = check_citations("It scored 999 [S1] and [S7].", passages)
        self.assertEqual(chk["status"], "cited-with-warnings")
        self.assertTrue(any("S7" in n for n in chk["notes"]))
        self.assertTrue(any("999" in n for n in chk["notes"]))

    def test_chat_routing(self):
        s = ChatSession(self.cfg, self.client, self.index)
        self.assertFalse(s.route("what can you help me with?")[0])
        self.assertFalse(s.route("make that shorter")[0])
        self.assertTrue(s.route("What learning rate did I use for my Pac-Man DQN project?")[0])
        s.turn("hello")
        rec = s.turn("make that shorter")
        self.assertEqual(rec["history_turns_sent"], 2)


if __name__ == "__main__":
    unittest.main()
