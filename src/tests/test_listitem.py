from src.simple_sharepoint.listitem import ListItem, AttributeMap
from src.simple_sharepoint.errors import SharePointListItemError
import responses
import unittest
from unittest import mock
from unittest.mock import MagicMock, call, patch


class TestListItem(unittest.TestCase):
    def setUp(self):
        self.from_dict_data = {"id": 1, "title": "Test Value"}
        self.list_item_from_dict = ListItem().from_dict(self.from_dict_data)

        self.attribute_maps = [
            AttributeMap("ID", "Id", True),
            AttributeMap("title", "Title", True),
        ]

        self.sp_list = MagicMock()
        self.sp_record = {"Id": 1, "Title": "Test Value"}
        self.list_item_from_sp = ListItem().from_sharepoint_record(
            self.sp_record, self.sp_list, self.attribute_maps
        )

        return super().setUp()

    def test_from_dict_has_lower_case_class_names(self):
        self.assertTrue(hasattr(self.list_item_from_dict, "id"))
        self.assertFalse(hasattr(self.list_item_from_dict, "ID"))

    def test_from_dict_has_correct_attributes(self):
        self.assertEqual(self.list_item_from_dict.id, self.from_dict_data.get("id"))
        self.assertEqual(
            self.list_item_from_dict.title, self.from_dict_data.get("title")
        )

    def test_from_dict_record_changes_empty(self):
        self.assertDictEqual({}, self.list_item_from_dict.record_changes)

    def test_from_dict_has_no_original(self):
        self.assertIsNone(self.list_item_from_dict.original_listitem)

    def test_from_dict_save_raise_error(self):
        with self.assertRaises(SharePointListItemError):
            self.list_item_from_dict.save()

    def test_from_sharepoint_has_lower_case_class_names(self):
        self.assertTrue(hasattr(self.list_item_from_sp, "id"))
        self.assertFalse(hasattr(self.list_item_from_sp, "ID"))

    def test_from_sharepoint_has_sharepoint_name_case_unchanged(self):
        self.assertTrue("Id" in self.list_item_from_sp._to_upload_format("all"))
        self.assertFalse("id" in self.list_item_from_sp._to_upload_format("all"))

    def test_from_sharepoint_has_correct_attributes(self):
        self.assertTrue(hasattr(self.list_item_from_sp, "id"))
        self.assertTrue(hasattr(self.list_item_from_sp, "title"))

    def test_from_sharepoint_has_changes(self):
        self.list_item_from_sp.id = 2
        self.assertDictEqual(self.list_item_from_sp.record_changes, {"Id": 2})
        self.list_item_from_sp.id = 1

    def test_from_sharepoint_can_save(self):
        self.list_item_from_sp.save(force_save=True)
        self.assertIn(
            call.update_list_item(1, {"Id": 1, "Title": "Test Value"}),
            self.sp_list.mock_calls,
        )
