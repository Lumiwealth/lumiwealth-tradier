import datetime as dt
from typing import Union

import pandas as pd

from .base import TradierApiBase


class Account(TradierApiBase):
    def __init__(self, account_number, auth_token, is_paper=True):
        TradierApiBase.__init__(self, account_number, auth_token, is_paper)

        # Account endpoints
        self.PROFILE_ENDPOINT = "v1/user/profile"  # GET
        self.ACCOUNT_BALANCE_ENDPOINT = f"v1/accounts/{account_number}/balances"  # GET
        self.ACCOUNT_GAINLOSS_ENDPOINT = f"v1/accounts/{account_number}/gainloss"  # GET
        self.ACCOUNT_HISTORY_ENDPOINT = f"v1/accounts/{account_number}/history"  # GET
        self.ACCOUNT_POSITIONS_ENDPOINT = f"v1/accounts/{account_number}/positions"  # GET
        self.ACCOUNT_INDIVIDUAL_ORDER_ENDPOINT = "v1/accounts/{account_id}/orders/{order_id}"  # GET

    def get_user_profile(self):
        """
        Fetch the user profile information from the Tradier Account API.

        This function makes a GET request to the Tradier Account API to retrieve the user profile
        information associated with the trading account linked to the provided credentials.
        The API response is expected to be in JSON format, containing details about the user profile.

        Returns:
            pandas.DataFrame: A DataFrame containing user profile information.

        Example:
            # Retrieve user profile information
            user_profile = get_user_profile()
            transposed_profile = user_profile.T  # Transpose the DataFrame for easy viewing.

        Example DataFrame (transposed):

            id              				id-sb-2r01lpprbg
            name               				Fat Albert
            account.account_number     		ABC1234567
            account.classification   		individual
            account.date_created  			2021-06-23T22:04:20.000Z
            account.day_trader              False
            account.option_level                6
            account.status                 	active
            account.type                   	margin
            account.last_update_date 		2021-06-23T22:04:20.000Z
        """
        data = self.request(endpoint=self.PROFILE_ENDPOINT)
        return pd.json_normalize(data["profile"])

    def get_account_balance(self) -> pd.DataFrame:
        """
        Fetch the account balance information from the Tradier Account API.

        This function makes a GET request to the Tradier Account API to retrieve the account
        balance information for the trading account associated with the provided credentials.
        The API response is expected to be in JSON format, containing details about the account
        balance.

        Returns:
            pandas.DataFrame: A DataFrame containing account balance information.

        Example:
            # Retrieve account balance information
            account_balance = get_account_balance()
            transposed_balance = account_balance.T  # Transpose the DataFrame for easy viewing.

        Example DataFrame (transposed):
                                    0
            option_short_value       -147.0
            total_equity           74314.82
            account_number       ABC1234567
            account_type             margin
            close_pl                      0
            current_requirement    17595.08
            equity                        0
            long_market_value      34244.16
            market_value           34097.16
            open_pl               -225300.265
            option_long_value        1054.0
            option_requirement       1000.0
            pending_orders_count          8
            short_market_value         -147.0
            stock_long_value        33190.16
            total_cash             40217.66
            uncleared_funds               0
            pending_cash            16892.9
            margin.fed_call               0
            margin.maintenance_call       0
            margin.option_buying_power 38919.84
            margin.stock_buying_power  77839.68
            margin.stock_short_value       0
            margin.sweep                   0
        """
        data = self.request(endpoint=self.ACCOUNT_BALANCE_ENDPOINT)
        return pd.json_normalize(data["balances"])

    def get_gainloss(self) -> pd.DataFrame:
        """
        Get cost basis information for a specific user account.
        This includes information for all closed positions.
        Cost basis information is updated through a nightly batch reconciliation process with tradier clearing firm.

        Returns:
            Pandas dataframe with columns [close_date, cost, gain_loss, gain_loss_percent, open_date, proceeds,
            quantity, symbol, term]

        Example:
            >>> account = Account(account_number='<account_id>', auth_token='<token>'
            >>> account.get_gainloss().head()
                    close_date      cost  gain_loss  gain_loss_percent proceeds  quantity          symbol  term
            0  2023-09-13T00:00:00.000Z  194700.0   -30600.0  -15.72  164100.0    10.0  LMT240119C00260000    19
            1  2023-09-13T00:00:00.000Z   10212.2     -432.6   -4.24    9779.6    20.0                KLAC     7
            2  2023-09-13T00:00:00.000Z    2300.0      175.0    7.61    2475.0    1.0   HAL251219C00018000    20
            3  2023-09-13T00:00:00.000Z   20700.0     1620.0    7.83   22320.0    9.0  H AL251219C00018000    20
            4  2023-09-06T00:00:00.000Z   16967.0     -193.0   -1.14   16774.0    100.0                TXN     5
        """
        data = self.request(endpoint=self.ACCOUNT_GAINLOSS_ENDPOINT)

        # If gainloss was not returned, return None
        if not data.get("gainloss"):
            return None

        # If there are no closed positions in the gailloss dict, return an empty dataframe
        if not isinstance(data["gainloss"], dict) or not data["gainloss"].get("closed_position"):
            return None

        return pd.json_normalize(data["gainloss"]["closed_position"])

    def get_history(
        self,
        start_date: Union[dt.datetime, dt.date, str, None] = None,
        end_date: Union[dt.datetime, dt.date, str, None] = None,
        limit: Union[int, None] = None,  # Tradier default if not specified is only 25
        activity_type: Union[str, None] = None,
        symbol: Union[str, None] = None,
    ) -> pd.DataFrame:
        """
        Get account activity history

        Args:
            start_date (dt.datetime | dt.date | str | None, optional): Start date for history. Defaults to None.
            end_date (dt.datetime | dt.date | str | None, optional): End date for history. Defaults to None.
            limit (int | None, optional): Number of rows to return. Defaults to 25 in Tradier itself.
            activity_type (str | None, optional): Type of activity to filter by. Valid values are:
                trade, option, ach, wire, dividend, fee, tax, journal, check, transfer, adjustment, interest
            symbol (str | None, optional): Symbol to filter by. Defaults to None.

        Returns:
            pd.DataFrame: DataFrame of account activity history. See Tradier documentation for details of columns
                returned.  https://documentation.tradier.com/brokerage-api/accounts/get-account-history

        """
        valid_activity_types = [
            "trade",
            "option",
            "ach",
            "wire",
            "dividend",
            "fee",
            "tax",
            "journal",
            "check",
            "transfer",
            "adjustment",
            "interest",
        ]
        params = {
            "start": self.date2str(start_date),
            "end": self.date2str(end_date),
        }

        if activity_type:
            if activity_type.lower() not in valid_activity_types:
                raise ValueError(f"activity_type ({activity_type}) must be one of {valid_activity_types}")
            params["type"] = activity_type.lower()

        if symbol:
            params["symbol"] = symbol.upper()

        if limit:
            params["limit"] = limit

        data = self.request(endpoint=self.ACCOUNT_HISTORY_ENDPOINT, params=params)
        return pd.json_normalize(data["history"]["event"])

    def get_positions(self, symbols=False, equities=False, options=False):
        """
        Fetch and filter position data from the Tradier Account API.

        This function makes a GET request to the Tradier Account API to retrieve position
        information related to a trading account. The API response is expected to be in
        JSON format, containing details about the positions held in the account.

        Args:
            symbols (list, optional): A list of trading symbols (e.g., stock ticker symbols)
                                        to filter the position data. If provided, only positions
                                        matching these symbols will be included.
            equities (bool, optional): If True, filter the positions to include only equities
                                        (stocks) with symbols less than 5 characters in length.
                                        If False, no filtering based on equities will be applied.
            options (bool, optional): If True, filter the positions to include only options
                                        with symbols exceeding 5 characters in length.
                                        If False, no filtering based on options will be applied.

        Returns:
            pandas.DataFrame: A DataFrame containing filtered position information based on
                                the specified criteria.

        Example:
            # Retrieve all positions without filtering
            all_positions = get_positions()

            # Retrieve positions for specific symbols ('AAPL', 'GOOGL')
            specific_positions = get_positions(symbols=['AAPL', 'GOOGL'])

            # Retrieve only equities
            equities_positions = get_positions(equities=True)

            # Retrieve only options
            options_positions = get_positions(options=True)
        """
        data = self.request(endpoint=self.ACCOUNT_POSITIONS_ENDPOINT)
        if data:
            # If there are no positions, return an empty DataFrame
            if not data.get("positions") or data["positions"] == "null":
                return pd.DataFrame()

            # Convert the position data to a list if it is not already (needed if exactly 1 position)
            position_data = data["positions"]["position"]
            if not isinstance(position_data, list):
                position_data = [position_data]

            # Create the DataFrame
            positions_df = pd.DataFrame(position_data)

            if symbols:
                positions_df = positions_df.query("symbol in @symbols")
            if equities:
                positions_df = positions_df[positions_df["symbol"].str.len() < 5]
                options = False
            if options:
                positions_df = positions_df[positions_df["symbol"].str.len() > 5]
            return positions_df
