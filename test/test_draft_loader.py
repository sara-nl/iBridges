import unittest
import os
from iBridges import get_draft_class


class TestDraftLoader(unittest.TestCase):
    def test_load_builtin_classes(self):
        draft_class = get_draft_class("CkanDraft", ["drafts"])
        self.assertEqual(draft_class.__module__, "ckandraft")
        self.assertEqual(draft_class.__name__, "CkanDraft")
        draft_class = get_draft_class("DataverseDraft", ["drafts"])
        self.assertEqual(draft_class.__module__, "dataversedraft")
        self.assertEqual(draft_class.__name__, "DataverseDraft")

    def test_load_plugin_class(self):
        search_path = os.path.join(os.path.dirname(__file__))
        draft_class = get_draft_class("CustomCkanDraft",
                                      ["drafts", search_path])

        self.assertEqual(draft_class.__module__, "customckandraft")
        self.assertEqual(draft_class.__name__, "CustomCkanDraft")

    def test_load_undefined_plugin_raises(self):
        search_path = os.path.join(os.path.dirname(__file__))
        with self.assertRaises(Exception):
            get_draft_class("XXX_CustomCkanDraft",
                            ["drafts", search_path])
