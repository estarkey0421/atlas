import importlib.util
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("atlas_validate", ROOT / "scripts" / "validate_data.py")
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


class AtlasValidatorTests(unittest.TestCase):
    def test_foundation_dataset_has_no_integrity_errors(self):
        result = mod.validate()
        self.assertEqual([], result.errors)
        self.assertEqual(10, result.counts["products"])
        self.assertEqual(10, result.counts["listings"])

    def test_item_id_parser_handles_weidian(self):
        self.assertEqual(
            "7161615777",
            mod.url_item_id("https://weidian.com/item.html?itemID=7161615777", "weidian"),
        )

    def test_score_validation(self):
        self.assertTrue(mod.valid_score(""))
        self.assertTrue(mod.valid_score("100"))
        self.assertFalse(mod.valid_score("101"))
        self.assertFalse(mod.valid_score("high"))


if __name__ == "__main__":
    unittest.main()
