class SpList():
    def __init__(self, site, title):
        self.site = site
        self.title = title
        self.base_url = "_api/web/lists/GetByTitle('{0}')".format(self.title)
        self.item_type = self.list_details["ListItemEntityTypeFullName"]

    @property
    def fields(self):
        url = self.base_url + "/fields"
        response = self.site.sp.get(url)

        return response.json().get('value')

    @property
    def list_details(self):
        return self.site.sp.get(self.base_url).json()

    def add_list_item(self,  json):
        url = self.base_url + "/items"
        response = self.site.sp.post(url, json=json)

        return response

    def create_field(self, field_name, field_enum, required=False, unique=False, static_name=None):
        from .field import FieldEnum

        if field_enum.value not in FieldEnum._value2member_map_:
            raise ValueError("field_enum must be a value in FieldEnum")

        url = self.base_url + "/Fields"

        update_data = {}
        update_data['__metadata'] = {'type': 'SP.Field'} #.format(field_enum.name)}
        update_data['Title'] = field_name
        update_data['FieldTypeKind'] = field_enum.value
        update_data['Required'] = required
        update_data['EnforceUniqueValues'] = unique
        update_data['StaticName'] = static_name

        response = self.site.sp.post(url, json=update_data)
        return response

    def delete_list_item(self, list_item_id):
        url = self.base_url + "/items({0})".format(list_item_id)
        response = self.site.sp.delete(url)

        return response

    def get_field(self, field_title):
        url = self.base_url + "/fields/GetByTitle('{0}')".format(field_title)

        response = self.site.sp.get(url)

        return response.json().get('value')

    def get_list_records(self, row_limit=5000):
        url = self.base_url + "/items?$top={0}".format(row_limit)

        response = self.site.sp.get(url)

        return response.json().get('value')

    def update_list_item(self, list_item_id, json):
        url = self.base_url + "/items({0})".format(list_item_id)
        response = self.site.sp.patch(url, json=json)

        return response
