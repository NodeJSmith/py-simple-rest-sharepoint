from src.simple_sharepoint.api import SharepointApi
import responses
import unittest
from unittest import mock
from unittest.mock import call, patch

site_url = "test.sharepoint.com"
client_id = ""
client_secret = ""


class TestApi(unittest.TestCase):
    @patch("src.simple_sharepoint.api.requests.get")
    def test_init_adds_proper_headers(self, req_get):
        api = SharepointApi(site_url, client_id, client_secret)
        calls = [call(f'https://{api.site_host}/_vti_bin/client.svc',
                      headers={'Authorization': 'bearer'}), call().headers.__contains__('WWW-Authenticate')]

        req_get.assert_has_calls(calls)

    def test_get_tenant_id_returns_proper_value(self):
        headers = {"WWW-Authenticate": 'Bearer realm="45ko8f6a-4g9e-4b0d-b164-d954lo574232",client_id="00000003-0000-0ff1-ce00-000000000000",authorization_uri="https://login.windows.net/common/oauth2/authorize"'}

        with patch("src.simple_sharepoint.api.requests.get") as p:
            api = SharepointApi(site_url, client_id, client_secret)

        with responses.RequestsMock() as rsps:
            rsps.add(
                "GET", url=f'https://{api.site_host}/_vti_bin/client.svc', headers=headers)
            val = api._get_tenant_id(api.site_host)
            self.assertEqual(val, "45ko8f6a-4g9e-4b0d-b164-d954lo574232")

    @patch("src.simple_sharepoint.api.requests.get")
    def test_get_session_mounts_adapters(self, req_get):
        api = SharepointApi(site_url, client_id, client_secret)

        with patch("src.simple_sharepoint.api.Session") as p:
            api._get_session()

        calls = [call(), call().mount("https://", mock.ANY),
                 call().mount("http://", mock.ANY)]

        p.assert_has_calls(calls)

    @patch("src.simple_sharepoint.api.requests.get")
    def test_set_initial_headers_has_contenttype_accept(self, req_get):
        api = SharepointApi(site_url, client_id, client_secret)

        with patch("src.simple_sharepoint.api.Session") as p:
            api._set_initial_headers(p)

        calls = [call.update({"Content-Type": "application/json",
                             "Accept": "application/json;odata=nometadata"})]
        p.headers.assert_has_calls(calls)

    @patch("src.simple_sharepoint.api.requests.get")
    def test_api_endpoint_returns_valid_uri(self, req_get):
        api = SharepointApi(site_url, client_id, client_secret)

        short_url = api._api_endpoint("_api/site")
        full_url = api._api_endpoint("https://{0}/_api/site".format(site_url))

        self.assertEqual(short_url, "_api/site")
        self.assertEqual(full_url, "https://{0}/_api/site".format(site_url))


if __name__ == '__main__':
    unittest.main()
