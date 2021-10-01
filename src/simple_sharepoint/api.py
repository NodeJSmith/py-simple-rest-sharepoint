"""
Module for low level SharePoint REST api interactions. This module contains the OAuth credentials for the QA SharePoint
site, the methods to get the header access token and the form digest value, as well as methods for update, add, and
delete SharePoint list items.

All requests are passed through the http variable, which is a requests session set up for automatic retries on certain
error codes.
"""

import urllib
from urllib.parse import urlparse
from datetime import datetime

from .errors import SharePointRequestError

import requests
from requests import Request, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BaseSharepointApi():
    def __init__(self, site_url, client_id, client_secret):
        self.token = None
        self.site_url = site_url
        self.site_host = urlparse(site_url).hostname
        self.tenant_id = self._get_tenant_id(self.site_host)
        self.client_id = client_id
        self.client_secret = client_secret
        self.quoted_client_secret = urllib.parse.quote(self.client_secret)

    @classmethod
    def _get_tenant_id(cls, site_host):
        url = f"https://{site_host}/_vti_bin/client.svc"
        headers = {"Authorization": "bearer"}

        resp = requests.get(url, headers=headers)

        return cls._process_realm_response(resp)

    @staticmethod
    def _process_realm_response(response):
        header_key = "WWW-Authenticate"
        if header_key in response.headers:
            auth_values = response.headers[header_key].split(",")
            bearer = auth_values[0].split("=")
            return bearer[1].replace('"', '')
        return None

    def _api_endpoint(self, url):
        """Convert a relative path such as /_api/web/lists to a full URI based
        on the site_url
        """
        if urllib.parse.urlparse(url).scheme in ['http', 'https']:
            return url  # url is already complete
        return urllib.parse.urljoin(self.site_url, url.lstrip('/'))

    def _set_initial_headers(self):
        raise NotImplementedError()

    def _get_header_access_token(self):
        raise NotImplementedError()

    def _update_headers(self, request):
        raise NotImplementedError()

    @property
    def contextinfo(self):
        raise NotImplementedError()

    def _get_session(self):
        raise NotImplementedError()

    def _send(self, request):
        raise NotImplementedError()

    def delete(self, url, **kwargs):
        raise NotImplementedError()

    def get(self, url, **kwargs):
        raise NotImplementedError()

    def patch(self, url, data=None, json=None, **kwargs):
        raise NotImplementedError()

    def post(self, url, data=None, json=None, **kwargs):
        raise NotImplementedError()

    def put(self, url, data=None, json=None, **kwargs):
        raise NotImplementedError()


class SharepointApi(BaseSharepointApi):
    def __init__(self, site_url, client_id, client_secret):
        super().__init__(site_url, client_id, client_secret)

        self._session = self._get_session()
        self._set_initial_headers(self._session)

    def _get_header_access_token(self):
        """Returns header access token - this token has to be included in every request to SharePoint """

        url = f"https://accounts.accesscontrol.windows.net/{self.tenant_id}/tokens/OAuth/2"

        data = f"""grant_type=client_credentials
                    &resource=00000003-0000-0ff1-ce00-000000000000/{self.site_host}@{self.tenant_id}
                    &client_id={self.client_id}@{self.tenant_id}
                    &client_secret={self.quoted_client_secret}"""

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        if not self.token or datetime.now() >= datetime.fromtimestamp(int(self.token['expires_on'])):
            self.token = requests.get(url, headers=headers, data=data).json()

        return ' '.join([self.token['token_type'], self.token['access_token']])

    def _get_session(self):
        requests_session = Session()

        # setting up HTTP adapter with retry built in
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT",
                             "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)

        requests_session.mount("https://", adapter)
        requests_session.mount("http://", adapter)

        return requests_session

    def _set_initial_headers(self, session):
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json;odata=nometadata'
        })

    def _update_headers(self, request):
        method_headers = {
            "POST": {"content-type": "application/json;odata=verbose",
                     "Accept": "application/json;odata=verbose",
                     "X-RequestDigest": self.contextinfo['FormDigestValue']},
            "DELETE": {
                'X-HTTP-Method': 'DELETE',
                'IF-MATCH': '*',
                "X-RequestDigest": self.contextinfo['FormDigestValue']},
            "PATCH": {
                'X-HTTP-Method': 'MERGE',
                'IF-MATCH': '*',
            }
        }

        if request.method in method_headers:
            request.headers.update(method_headers[request.method])

        request.headers.setdefault(
            'Accept', 'application/json;odata=nometadata')

        request.headers.setdefault('Content-Type', 'application/json')

        return request

    def _send(self, request):
        try:
            request.url = self._api_endpoint(request.url)

            # this one is set for the whole session
            access_token = self._get_header_access_token()
            if access_token != self._session.headers.get('Authorization'):
                self._session.headers['Authorization'] = access_token

            request = self._session.prepare_request(request)
            request = self._update_headers(request)

            resp = self._session.send(request)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as err:
            raise SharePointRequestError(
                "SharePoint {0} request failed".format(request.method), err)

    @property
    def contextinfo(self):
        response = self._session.post(self.site_url + "/_api/contextinfo")
        data = response.json()
        return data

    def delete(self, url, **kwargs):
        request = Request('DELETE', url, **kwargs)

        return self._send(request)

    def get(self, url, **kwargs):
        request = Request('GET', url, **kwargs)
        return self._send(request)

    def patch(self, url, data=None, json=None, **kwargs):
        request = Request(
            'PATCH', url, data=data, json=json, **kwargs)

        return self._send(request)

    def post(self, url, data=None, json=None, **kwargs):
        request = Request(
            'POST', url, data=data, json=json, **kwargs)
        return self._send(request)

    def put(self, url, data=None, json=None, **kwargs):
        request = Request('PUT', url, data=data, json=json, **kwargs)
        return self._send(request)
