import datetime as dt
import json
from typing import Union, List
import logging
from time import sleep

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Define base url for live/paper trading and individual API endpoints
TRADIER_LIVE_URL = "https://api.tradier.com"
TRADIER_SANDBOX_URL = "https://sandbox.tradier.com"

DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_FACTOR = 3.06
DEFAULT_RETRY_WAIT_SECONDS = 3
DEFAULT_CONNECTION_TIMEOUT = 10
DEFAULT_RETRY_HTTP_STATUS_CODES: List[int] = [409, 429, 500, 502, 503, 504, 520, 530]
# Don't retry these as they are not transient errors:
# 401 - Unauthorized

# https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.retry.Retry
DEFAULT_ALLOWED_METHODS = frozenset(['GET'])
# Retry all methods
# DEFAULT_ALLOWED_METHODS = None

logger = logging.getLogger(__name__)


class TradierApiError(Exception):
    pass


class TradierApiBase:
    def __init__(self, account_number, auth_token, is_paper=True):
        self.is_paper = is_paper

        # Define account credentials
        self.ACCOUNT_NUMBER = account_number
        self.AUTH_TOKEN = auth_token
        self.REQUESTS_HEADERS = {
            "Authorization": f"Bearer {self.AUTH_TOKEN}",
            "Accept": "application/json",  # Default all interactions with Tradier API to return json
        }

        # Create a session object for retrying requests
        self._session = requests.Session()

    def base_url(self):
        """
        This function returns the base url for the Tradier API.
        """
        if self.is_paper:
            return TRADIER_SANDBOX_URL
        else:
            return TRADIER_LIVE_URL

    @staticmethod
    def date2str(date: Union[str, dt.datetime, dt.date], include_min=False) -> str:
        """
        This function converts a date object to a string in the format of YYYY-MM-DD.
        :param date: datetime.date object
        :param include_min: Include minutes in the string. Default is False.
        :return: String in the format of YYYY-MM-DD or YYYY-MM-DD HH:MM
        """
        format_str = "%Y-%m-%d" if not include_min else "%Y-%m-%d %H:%M"
        if isinstance(date, dt.datetime | dt.date):
            return date.strftime(format_str)
        return date

    def delete(self, endpoint, params=None, headers=None, data=None) -> dict:
        """
        This function makes a DELETE request to the Tradier API and returns a json object.
        :param endpoint:  Tradier API endpoint
        :param params:  Dictionary of requests.delete() parameters to pass to the endpoint
        :param headers:  Dictionary of requests.delete() headers to pass to the endpoint
        :param data:  Dictionary of requests.delete() data to pass to the endpoint
        :return:  json object
        """
        return self.request(endpoint, params=params, headers=headers, data=data, method="delete")

    def request(
            self,
            endpoint,
            params=None,
            headers=None,
            data=None,
            required_response_key=None,
            method="get"
    ) -> dict:
        """
        This function makes a request to the Tradier API and returns a json object.
        :param endpoint: Tradier API endpoint
        :param params: Dictionary of requests.get() parameters to pass to the endpoint
        :param headers: Dictionary of requests.get() headers to pass to the endpoint
        :param data: Dictionary of requests.post() data to pass to the endpoint
        :param method: 'get', 'post' or 'delete'
        :param required_response_key: Key that must be in the data response else it retries the request
        :return: json object
        """
        if not headers:
            headers = self.REQUESTS_HEADERS

        if not params:
            params = {}

        if not data:
            data = {}

        # We want to retry GET requests if the response is empty or if the request fails.
        # We don't want to retry other methods because they may have side effects (like submitting
        # extra orders).
        # We use simple a for loop to catch cases when the request succeeds but there was no data.
        retry_attempts = DEFAULT_RETRY_ATTEMPTS if method == "get" else 1
        for retry_attempt in range(retry_attempts):
            r = None
            if method == "get":
                # We use a retry session to handle transient errors and retry the request.
                r = self.requests_retry_session().get(
                    url=f"{self.base_url()}/{endpoint}",
                    params=params,
                    headers=headers,
                    timeout=DEFAULT_CONNECTION_TIMEOUT,
                )
            elif method == "post":
                r = requests.post(url=f"{self.base_url()}/{endpoint}", params=params, headers=headers, data=data)
            elif method == "put":
                r = requests.put(url=f"{self.base_url()}/{endpoint}", params=params, headers=headers, data=data)
            elif method == "delete":
                r = requests.delete(url=f"{self.base_url()}/{endpoint}", params=params, data=data, headers=headers)
            else:
                raise ValueError(f"Invalid method {method}. Must be one of ['get', 'post', 'put', 'delete']")

            # Check for errors in response from Tradier API.
            # 502 is a common error code when the API is down for a few seconds so we ignore it too.
            if r.status_code != 200 and r.status_code != 201 and r.status_code != 502:
                raise TradierApiError(f"Error: {r.status_code} - {r.text}")

            # Parse the response from the Tradier API.  Sometimes no valid json is returned.
            try:
                ret_data = r.json()
            except json.decoder.JSONDecodeError as  e:
                logger.warning(f"Failed to decode JSON response: {e}")
                ret_data = {}

            if required_response_key:
                if required_response_key in ret_data and ret_data[required_response_key] is not None:
                    break
                else:
                    if retry_attempt == retry_attempts - 1:
                        logger.error(f"Response from {endpoint} did not contain {required_response_key}.")
                    else:
                        logger.info(f"Response from {endpoint} did not contain {required_response_key}. Retrying...")
                        sleep(DEFAULT_RETRY_WAIT_SECONDS)

        if ret_data and "errors" in ret_data and "error" in ret_data["errors"]:
            if isinstance(ret_data["errors"]["error"], list):
                msg = " | ".join(ret_data["errors"]["error"])
            else:
                msg = ret_data["errors"]["error"]
            raise TradierApiError(f"Error: {msg}")

        return ret_data

    def send(self, endpoint, data, headers=None, method="post") -> dict:
        """
        This function sends a post request to the Tradier API and returns a json object.
        :param endpoint: Tradier API endpoint
        :param data: Dictionary of requests.post() data to pass to the endpoint
        :param headers: Dictionary of requests.post() headers to pass to the endpoint
        :return: json object
        """
        if method.lower() not in ["put", "post"]:
            raise ValueError(f"Invalid method {method}. Must be one of ['put', 'post']")
        return self.request(endpoint, params={}, headers=headers, data=data, method=method.lower())

    def requests_retry_session(
            self,
            retries=DEFAULT_RETRY_ATTEMPTS,
            backoff_factor=DEFAULT_RETRY_BACKOFF_FACTOR,
            status_forcelist=None,
            allowed_methods=DEFAULT_ALLOWED_METHODS,
            session=None,
    ):
        if status_forcelist is None:
            status_forcelist = DEFAULT_RETRY_HTTP_STATUS_CODES
            
        session = session or self._session
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=allowed_methods,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
