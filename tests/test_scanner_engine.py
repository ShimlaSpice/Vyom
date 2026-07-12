"""Tests for the modular scanner architecture."""

from __future__ import annotations

import unittest

from app.scanner.scanner import ScannerEngine


class ScannerEngineTests(unittest.TestCase):
    """Validate the scanner workflow with mock data."""

    def test_scan_returns_ranked_candidates(self) -> None:
        """The scanner should score and rank mock stock candidates."""

        engine = ScannerEngine()
        results = engine.scan(limit=3)

        self.assertLessEqual(len(results), 3)
        self.assertTrue(results)
        self.assertEqual(results[0]["symbol"], "RELIANCE")
        self.assertGreaterEqual(results[0]["score"], 0)
        self.assertLessEqual(results[0]["score"], 100)


if __name__ == "__main__":
    unittest.main()
