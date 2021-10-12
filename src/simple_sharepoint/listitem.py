from simple_sharepoint.errors import SharePointListItemError

from collections.abc import Iterable
from copy import copy


class AttributeMap:
    """
    Provides mapping between a SharePoint field internal name and
    the attribute name in the ListItem object. All attribute names
    are forced into lowercase. The include_in_output argument allows
    you to mark if fields should not be written back to SharePoint
    """

    def __init__(self, class_name, sharepoint_name, include_in_output):
        self.class_name = class_name
        self.sharepoint_name = sharepoint_name
        self.include_in_output = include_in_output

    @classmethod
    def attribute_map_list_from_list(cls, list_of_items):
        """
        Given a list of tuples or lists of length 3, creates
        an attribute map for each record and returns the list
        of attribute maps
        """
        return_list = list()

        if not isinstance(list_of_items, Iterable):
            list_of_items = [
                list_of_items,
            ]

        for x in list_of_items:
            new_item = cls.__new__(cls)
            try:
                new_item.class_name = x[0]
                new_item.sharepoint_name = x[1]
                new_item.include_in_output = x[2]
                return_list.append(new_item)
            except:
                pass

        return return_list

    @classmethod
    def from_dict(cls, map_dict):
        new_item = cls.__new__(cls)
        new_item.class_name = map_dict.get("class_name")
        new_item.sharepoint_name = map_dict.get("sharepoint_name")
        new_item.include_in_output = map_dict.get("include_in_output")

        return new_item

    @property
    def class_name(self):
        return None if self._class_name is None else self._class_name.lower()

    @class_name.setter
    def class_name(self, val):
        self._class_name = val


class ListItem(object):
    """The logical structure of SharePoint list item

    This class links SharePoint data to class attributes from the passed in AttributeMap
    This allows you to define your own python class attributes while still allowing
    you to push changes to Sharepoint with the proper Sharepoint field names
    """

    def __init__(self):
        self._attribute_map = None
        self.sp_list = None
        self.id = None
        self._original_listitem = None

    @classmethod
    def from_sharepoint_record(cls, record, sp_list, attribute_map):
        list_item = cls()
        list_item.sp_list = sp_list
        list_item._attribute_map = attribute_map
        includes_id = False
        for x in list_item._attribute_map:
            setattr(list_item, x.class_name, record.get(x.sharepoint_name))
            if not includes_id and x.sharepoint_name.lower() == "id":
                includes_id = True

        if not includes_id:
            list_item.id = record.get("Id")

        list_item._original_listitem = copy(list_item) if list_item.id else None

        return list_item

    @classmethod
    def from_dict(cls, record, sp_list=None, attribute_map=None):
        if bool(sp_list) ^ bool(attribute_map):
            raise SharePointListItemError(
                "You must either pass both sp_list and attribute_map or neither"
            )
        list_item = cls()
        if sp_list:
            list_item.sp_list = sp_list

        if attribute_map:
            list_item._attribute_map = attribute_map

        for k, v in record.items():
            setattr(list_item, k.lower(), v)

        return list_item

    def update_from_dict(self, newdata):
        for key, value in newdata.items():
            setattr(self, key, value)

    def update_from_sp_record(self, sp_record):
        for x in self._attribute_map:
            setattr(self, x.class_name, sp_record.get(x.sharepoint_name))

    def update_from_list_item(self, list_item):
        for x in self._attribute_map:
            setattr(self, x.class_name, getattr(list_item, x.class_name))

    def duplicate(self):
        new_listitem = copy(self)
        if hasattr(self, "id"):
            new_listitem.id = None

        new_listitem._original_listitem = None

        return new_listitem

    def save(self, force_save=False):
        if self.sp_list is None:
            raise SharePointListItemError(
                "A SharePoint list must be set in order to save a ListItem"
            )
        if self.id is None:
            json = self._to_upload_format("new")
            resp = self.sp_list.add_list_item(json)
            return resp

        if force_save:
            json = self._to_upload_format("all")
        else:
            json = self._to_upload_format("change")

        if json:
            resp = self.sp_list.update_list_item(self.id, json)

            return resp

    def delete(self):
        self.sp_list.delete_list_item(self.id)

    def _to_upload_format(self, record_type):
        """Creates a dictionary object based on the record_type: changes, new, all

        Dictionary is handled differently depending on the record type:
            *New removes the Id if there is one and adds the ListItemType
            *Changes only include attributes that have changed
            *All includes everything

        :param record_type: str: changes, new, or all

        :returns: dict

        :raises: ValueError
        """

        if not self._attribute_map:
            return {}

        record_dict = {}

        if record_type not in ["change", "new", "all"]:
            raise ValueError(
                "record_type parameter not valid, must be 'change', 'new', or 'all'"
            )

        # if changes, only include changed values
        if record_type == "change":
            record_dict = self.record_changes

        else:  # otherwise, include everything - difference between "new" and "all" is handled in next step
            for x in self._attribute_map:
                record_dict[x.sharepoint_name] = getattr(self, x.class_name)

        # if new then remove the Id field (new values don't have an Id), set the list_item_type in the metadata, and
        # set the Title field to the EID
        if record_type == "new":
            record_dict["__metadata"] = {"type": self.sp_list.item_type}
            if "Id" in record_dict:
                record_dict.pop("Id")
            record_dict.setdefault("Title", "New Record")
        # else:
        #     if record_dict and "Id" not in record_dict:
        #         record_dict["Id"] = self.id

        return record_dict

    @property
    def record_changes(self):
        """Property that creates dictionary that includes the fields that have been changed based on attribute maps

        :returns: dict
        """
        if not self._attribute_map:
            return {}

        sp_dict = {}
        for x in self._attribute_map:
            if x.include_in_output and self.property_has_changed(x.class_name):
                sp_dict[x.sharepoint_name] = getattr(self, x.class_name)

        return sp_dict

    def property_has_changed(self, class_name):
        if (
            self.original_listitem is None
        ):  # if no original_listitem then it is by default a change
            return True

        for x in self._attribute_map:
            if class_name == x.class_name:
                return getattr(self, class_name) != getattr(
                    self.original_listitem, class_name
                )

    @property
    def has_changed(self):
        """Property that checks if current object matches original object

        :returns: bool
        """

        if self.original_listitem and self.original_listitem._to_upload_format(
            "all"
        ) == self._to_upload_format("all"):
            return False
        else:
            return True

    @property
    def original_listitem(self):
        return self._original_listitem

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)
