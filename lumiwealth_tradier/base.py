import datetime as dt
from typing import Union

import requests

# Define base url for live/paper trading and individual API endpoints
TRADIER_LIVE_URL = "https://api.tradier.com"
TRADIER_SANDBOX_URL = "https://sandbox.tradier.com"


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
        This function converts a datetime.date object to a string in the format of YYYY-MM-DD.
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

    def request(self, endpoint, params=None, headers=None, data=None, method="get") -> dict:
        """
        This function makes a request to the Tradier API and returns a json object.
        :param endpoint: Tradier API endpoint
        :param params: Dictionary of requests.get() parameters to pass to the endpoint
        :param headers: Dictionary of requests.get() headers to pass to the endpoint
        :param data: Dictionary of requests.post() data to pass to the endpoint
        :param method: 'get', 'post' or 'delete'
        :return: json object
        """
        if not headers:
            headers = self.REQUESTS_HEADERS

        if not params:
            params = {}

        if not data:
            data = {}

        if method == "get":
            r = requests.get(url=f"{self.base_url()}/{endpoint}", params=params, headers=headers)
        elif method == "post":
            r = requests.post(url=f"{self.base_url()}/{endpoint}", params=params, headers=headers, data=data)
        elif method == "delete":
            r = requests.delete(url=f"{self.base_url()}/{endpoint}", params=params, data=data, headers=headers)
        else:
            raise ValueError(f"Invalid method {method}. Must be one of ['get', 'post', 'delete']")

        # Check for errors in response
        if r.status_code != 200:
            raise TradierApiError(f"Error: {r.status_code} - {r.text}")

        ret_data = r.json()
        if ret_data and "errors" in ret_data and "error" in ret_data["errors"]:
            if isinstance(ret_data["errors"]["error"], list):
                msg = " | ".join(ret_data["errors"]["error"])
            else:
                msg = ret_data["errors"]["error"]
            raise TradierApiError(f"Error: {msg}")

        return r.json()

    def send(self, endpoint, data, headers=None) -> dict:
        """
        This function sends a post request to the Tradier API and returns a json object.
        :param endpoint: Tradier API endpoint
        :param data: Dictionary of requests.post() data to pass to the endpoint
        :param headers: Dictionary of requests.post() headers to pass to the endpoint
        :return: json object
        """
        return self.request(endpoint, params={}, headers=headers, data=data, method="post")
