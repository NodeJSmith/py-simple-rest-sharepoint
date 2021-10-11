from src.simple_sharepoint.api import SharepointApi
from src.simple_sharepoint.site import Site
import responses
import unittest
from unittest import mock
from unittest.mock import call, patch

site_url = ""
client_id = ""
client_secret = ""

@patch("src.simple_sharepoint.api.requests.get")
class TestSite(unittest.TestCase):
    def test_context_info_matches_api_context_info(self, req_get):
        with patch("src.simple_sharepoint.api.Session") as p:        
            api = SharepointApi(site_url, client_id, client_secret)
            site = Site(api)

        self.assertEqual(site.contextinfo, api.contextinfo)

    def test_info_property_endpoint(self, req_get):
        with patch("src.simple_sharepoint.api.Session") as p:
            api = SharepointApi(site_url, client_id, client_secret)
            site = Site(api)
            with patch("src.simple_sharepoint.api.SharepointApi._get_header_access_token") as hat:
                site.info

        p.assert_has_calls([call().post("/_api/contextinfo")])


if __name__ == '__main__':
    unittest.main()
