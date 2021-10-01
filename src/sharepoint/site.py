"""
Module for higher level SharePoint REST api actions - utilize methods in the api.py module
"""


class Site():
    def __init__(self, sp):
        self.sp = sp

    @property
    def info(self):
        endpoint = "_api/site"
        value = self.sp.get(endpoint).json()
        return value

    @property
    def web(self):
        endpoint = "_api/web"
        value = self.sp.get(endpoint).json()
        return value

    @property
    def contextinfo(self):
        return self.sp.contextinfo

    @property
    def contenttypes(self):
        endpoint = "_api/web/contenttypes"
        value = self.sp.get(endpoint).json().get('value')
        return value

    @property
    def eventreceivers(self):
        endpoint = "_api/web/eventreceivers"
        value = self.sp.get(endpoint).json().get('value')
        return value

    @property
    def features(self):
        endpoint = "_api/web/features"
        value = self.sp.get(endpoint).json().get('value')
        return value

    @property
    def fields(self):
        endpoint = "_api/web/fields"
        value = self.sp.get(endpoint).json().get('value')
        return value

    @property
    def lists(self):
        endpoint = "_api/web/lists"
        value = self.sp.get(endpoint).json().get('value')
        return value

    @property
    def siteusers(self):
        endpoint = "_api/web/siteusers"
        value = self.sp.get(endpoint).json().get('value')
        return value

    @property
    def groups(self):
        endpoint = "_api/web/sitegroups"
        value = self.sp.get(endpoint).json().get('value')
        return value

    @property
    def roleassignments(self):
        endpoint = "_api/web/roleassignments"
        value = self.sp.get(endpoint).json().get('value')
        return value

    # def set_title_field_to_optional(self, list_title):
    #     """Sets the Title field in the given list to optional

    #     :param list_title: str: title of SharePoint list
    #     """

    #     # TODO - this likely is not necessary anymore, since we are not creating new lists

    #     field_rec = [x for x in self.get_field(list_title)
    #                  if x['InternalName'] == "Title"][0]

    #     if field_rec and field_rec.get('Required'):
    #         body = {'Required': False}
    #         self.update_list_field(field_rec, list_title, body)

    # def check_field_exists(self, list_title, field_title):
    #     """Check that a field exists to avoid error from attempting to access non-existent field

    #     :param list_title: str: title of SharePoint list
    #     :param field_title: str: title of field in SharePoint list

    #     :returns: bool
    #     """

    #     field_rec = self._get_first_or_none(
    #         "InternalName", field_title, list_data=self.get_list_fields(list_title))

    #     return field_rec is not None

    # def update_list_field(self, field_rec, list_title, body):
    #     """Given a field record, a list title, and the json body to update with, updates the SharePoint list field

    #     :param field_rec: dict: field record from SharePoint field query
    #     :param list_title: str: title of SharePoint list
    #     :param body: dict: dictionary structured for SharePoint REST api fields endpoint
    #     """

    #     field_id = field_rec.get('Id')
    #     update_field_url = "_api/web/lists/GetByTitle('{0}')/fields('{1}')".format(
    #         list_title, field_id)

    #     response = self.sp.post(url=update_field_url, json=body)

    #     response.raise_for_status()

    # def get_email_from_sharepoint_id(self, sharepoint_id: int):
    #     """Returns email address from a SharePoint integer user id value

    #     :param sp_user_id: int: SharePoint user id

    #     :returns: str
    #     """

    #     return self._get_first_or_none("Id", sharepoint_id, list_data=self.siteusers).get("Email")

    # def get_sharepoint_id_from_email(self, email):
    #     """Returns SharePoint integer user ID from an email address

    #     :param username: str: email address

    #     :returns: int
    #     """

    #     return self._get_first_or_none("Email", email, list_data=self.siteusers).get("Id")

    def _get_first_or_none(self, compare_column, compare_value, list_data=None, url=None):
        if not list_data and not url:
            return ValueError("either list_data or url must be provided")

        if not list_data:
            list_data = self.sp.get(url).json().get('value')

        try:
            return [x for x in list_data if x[compare_column] == compare_value][0]
        except IndexError as e:
            return None

    # TODO Add large file upload with chunking
    # https://github.com/JonathanHolvey/sharepy/issues/23
