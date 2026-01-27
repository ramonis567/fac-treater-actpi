import unittest
from app.logic.processor import split_tag

class TestSplitTag(unittest.TestCase):
    def test_basic_split(self):
        code, desc = split_tag("TAG123 - Description")
        self.assertEqual(code, "TAG123")
        self.assertEqual(desc, "Description")

    def test_split_with_spaces(self):
        code, desc = split_tag("  TAG123  -  Description  ")
        self.assertEqual(code, "TAG123")
        self.assertEqual(desc, "Description")

    def test_no_separator(self):
        code, desc = split_tag("TAG_ONLY")
        self.assertEqual(code, "TAG_ONLY")
        self.assertEqual(desc, "")

    def test_none(self):
        code, desc = split_tag(None)
        self.assertEqual(code, "")
        self.assertEqual(desc, "")

    def test_nan(self):
        code, desc = split_tag("nan")
        self.assertEqual(code, "")
        self.assertEqual(desc, "")

        code, desc = split_tag("NAN")
        self.assertEqual(code, "")
        self.assertEqual(desc, "")

    def test_multiple_separators(self):
        code, desc = split_tag("TAG - Desc - Extra")
        self.assertEqual(code, "TAG")
        self.assertEqual(desc, "Desc - Extra")

if __name__ == "__main__":
    unittest.main()
