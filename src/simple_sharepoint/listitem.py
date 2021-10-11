from collections import namedtuple
from copy import copy

AttributeMap = namedtuple(
    "AttributeMap", ["sharepoint_name", "class_name", "include_in_output"])


class ListItem(object):
    """The logical structure of SharePoint list item

    This class links SharePoint data to class attributes from the passed in AttributeMap
    This allows you to define your own python class attributes while still allowing
    you to push changes to Sharepoint with the proper Sharepoint field names
    """

    def __init__(self, sp_list, attribute_map, record):
        self._attribute_map = attribute_map
        self.sp_list = sp_list
        self.id = None

        includes_id = False
        for x in self._attribute_map:
            setattr(self, x.class_name, record.get(x.sharepoint_name))
            if not includes_id and x.sharepoint_name.lower() == "id":
                includes_id = True

        if not includes_id:
            self.id = record.get("Id")

        self._original_listitem = copy(self) if self.id else None

    def duplicate(self):
        new_listitem = copy(self)
        if hasattr(self, 'id'):
            new_listitem.id = None

        new_listitem._original_listitem = None

        return new_listitem

    def save(self, force_save=False):
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

        record_dict = {}

        if record_type not in ['change', 'new', 'all']:
            raise ValueError(
                "record_type parameter not valid, must be 'change', 'new', or 'all'")

        # if changes, only include changed values
        if record_type == "change":
            record_dict = self.record_changes

        else:  # otherwise, include everything - difference between "new" and "all" is handled in next step
            for x in self._attribute_map:
                record_dict[x.sharepoint_name] = getattr(self, x.class_name)

        # if new then remove the Id field (new values don't have an Id), set the list_item_type in the metadata, and
        # set the Title field to the EID
        if record_type == "new":
            record_dict['__metadata'] = {"type": self.sp_list.item_type}
            if "Id" in record_dict:
                record_dict.pop('Id')
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

        sp_dict = {}
        for x in self._attribute_map:
            if x.include_in_output and self.property_has_changed(x.class_name):
                sp_dict[x.sharepoint_name] = getattr(self, x.class_name)

        return sp_dict

    def property_has_changed(self, class_name):
        if self.original_listitem is None:  # if no original_listitem then it is by default a change
            return True

        for x in self._attribute_map:
            if class_name == x.class_name:
                return getattr(self, class_name) != getattr(self.original_listitem, class_name)

    @property
    def has_changed(self):
        """Property that checks if current object matches original object

         :returns: bool
         """

        if self.original_listitem and self.original_listitem._to_upload_format("all") == self._to_upload_format("all"):
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
