import datetime as dt
from typing import Union

import pandas as pd

from .base import TradierApiBase


class MarketData(TradierApiBase):
    """
    Market Data API endpoints for Tradier API.

    Tradier API Documentation:
    https://documentation.tradier.com/brokerage-api/markets/get-quotes
    """

    def __init__(self, account_number, auth_token, is_paper=True):
        TradierApiBase.__init__(self, account_number, auth_token, is_paper)

        # Account endpoints
        self.QUOTES_ENDPOINT = "v1/markets/quotes"
        self.HISTORICAL_QUOTES_ENDPOINT = "v1/markets/history"
        self.TIME_AND_SALES_ENDPOINT = "v1/markets/timesales"
        self.OPTION_CHAIN_ENDPOINT = "v1/markets/options/chains"
        self.OPTION_STRIKES_ENDPOINT = "v1/markets/options/strikes"
        self.OPTION_EXPIRATIONS_ENDPOINT = "v1/markets/options/expirations"
        self.OPTION_SYMBOL_ENDPOINT = "v1/markets/options/lookup"
        self.CLOCK_ENDPOINT = "v1/markets/clock"
        self.CALENDAR_ENDPOINT = "v1/markets/calendar"
        self.SEARCH_ENDPOINT = "v1/markets/search"  # Companies lookup
        self.LOOKUP_SYMBOL_ENDPOINT = "v1/markets/lookup"

    # Create functions for each endpoint
    def get_quotes(self, symbols: Union[str, list[str]], greeks=False) -> pd.DataFrame:
        # noinspection PyShadowingNames
        """
        Get quotes for a list of symbols.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/get-quotes

        Example:
            >>> from lumiwealth_tradier import Tradier
            >>> tradier = Tradier('ACCOUNT_NUMBER', 'AUTH_TOKEN')
            >>> quotes = tradier.market.get_quotes(['AAPL', 'MSFT'])
            >>> apple_price = quotes.loc['AAPL']['last']

        :param symbols: List of symbols to get quotes for.
        :param greeks: Include greeks in response. Only Valid for Options.
        :return: DataFrame of quotes.  See Tradier weblink for column definitions.
        """
        # Create payload
        symbols = symbols if isinstance(symbols, str) else ",".join(symbols)
        payload = {"symbols": symbols, greeks: greeks}

        # Get response
        response = self.request(self.QUOTES_ENDPOINT, payload)

        if "quote" not in response["quotes"]:
            raise ValueError(f"Invalid symbol: {payload['symbols']}")

        # Parse response - single Symbol doesn't return a list from the API, multiple symbols do
        quotes = response["quotes"]["quote"]
        quotes = quotes if isinstance(quotes, list) else [quotes]
        df = pd.json_normalize(quotes)

        return df.set_index("symbol")

    def get_last_price(self, symbol: str) -> float:
        """
        Get the last price for a symbol.
        :param symbol: Symbol to get the last price for.
        :return: Last price for the symbol.
        """
        return self.get_quotes(symbol).loc[symbol]["last"]

    def get_historical_quotes(
        self,
        symbol: str,
        interval: str = "daily",
        session_filter: str = "open",
        start_date: Union[dt.datetime, dt.date, str, None] = None,
        end_date: Union[dt.datetime, dt.date, str, None] = None,
    ) -> pd.DataFrame:
        """
        Get historical quotes for a symbol.  This is for large timescale aggregation of daily or more.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/get-history

        :param symbol: Symbol to get historical quotes for.
        :param interval: Interval for historical quotes. Valid values are: daily, weekly, monthly.
        :param session_filter: Specify to retrieve aggregate data for all hours of the day (all) or only
                regular trading sessions (open). Valid values are: all, open
        :param start_date: Start date for historical quotes. Format is YYYY-MM-DD.
        :param end_date: End date for historical quotes. Format is YYYY-MM-DD.

        :return: DataFrame of historical quotes. See Tradier weblink for column definitions.
        """
        valid_intervals = ["daily", "weekly", "monthly"]
        if interval.lower() not in valid_intervals:
            raise ValueError(f"Invalid interval {interval}. Valid intervals are {valid_intervals}")

        valid_session_filters = ["all", "open"]
        if session_filter.lower() not in valid_session_filters:
            raise ValueError(
                f"Invalid session_filter {session_filter}. Valid session_filters are " f"{valid_session_filters}"
            )

        # Create payload
        payload = {
            "symbol": symbol,
            "interval": interval.lower(),
            "session_filter": session_filter.lower(),
        }
        if start_date:
            payload["start"] = self.date2str(start_date)
        if end_date:
            payload["end"] = self.date2str(end_date)

        # Get response
        response = self.request(self.HISTORICAL_QUOTES_ENDPOINT, payload)

        if response["history"] is None or "day" not in response["history"]:
            raise LookupError(
                f"No Historical Data found for: Symbol={payload['symbol']}, start={payload['start']}, "
                f"end={payload['end']}"
            )

        # Parse response
        quotes = response["history"]["day"]
        quotes = quotes if isinstance(quotes, list) else [quotes]
        df = pd.json_normalize(quotes)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df.set_index("date")

    def get_timesales(
        self,
        symbol: str,
        interval: int = 1,
        start_date: Union[dt.datetime, dt.date, str, None] = None,
        end_date: Union[dt.datetime, dt.date, str, None] = None,
        session_filter: str = "open",
    ) -> pd.DataFrame:
        """
        Get time and sales for a symbol. This is for small timescale aggregation of less than a day. Can only look
        back 20 days from today.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/get-timesales

        :param symbol: Symbol to get time and sales for.
        :param interval: Interval in minutes for time and sales. Valid values are: 1, 5, 15
        :param start_date: Start date for time and sales. Format is YYYY-MM-DD HH:MM.
        :param end_date: End date for time and sales. Format is YYYY-MM-DD HH:MM.
        :param session_filter: Specify to retrieve aggregate data for all hours of the day (all) or only
                regular trading sessions (open). Valid values are: all, open
        :return: DataFrame of time and sales. See Tradier weblink for column definitions.
        """
        if interval not in [1, 5, 15]:
            raise ValueError(f"Invalid interval {interval}. Valid intervals are 1, 5, 15")

        valid_session_filters = ["all", "open"]
        if session_filter.lower() not in valid_session_filters:
            raise ValueError(
                f"Invalid session_filter {session_filter}. Valid session_filters are " f"{valid_session_filters}"
            )

        # Create payload
        payload = {
            "symbol": symbol,
            "interval": f"{interval}min",
            "session_filter": session_filter.lower(),
        }
        if start_date:
            payload["start"] = self.date2str(start_date, include_min=True)
        if end_date:
            payload["end"] = self.date2str(end_date, include_min=True)

        response = self.request(self.TIME_AND_SALES_ENDPOINT, payload)
        if response["series"] is None or "data" not in response["series"]:
            raise LookupError(
                f"No Time and Sales found for: Symbol={payload['symbol']}, start={payload['start']}, "
                f"end={payload['end']}"
            )

        quotes = response["series"]["data"]
        quotes = quotes if isinstance(quotes, list) else [quotes]  # Can happen if start == end
        df = pd.json_normalize(quotes)
        df["datetime"] = pd.to_datetime(df["time"]).dt.tz_localize("US/Eastern")
        return df.set_index("datetime")

    def get_option_expirations(
        self, symbol: str, strikes=True, contract_size=True, expiration_type=True, include_all_roots=False
    ) -> pd.DataFrame:
        """
        Get option expirations for a symbol.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/options/get-options-expirations

        DataFrame Format:
                        contract_size   expiration_type                      strikes
            date
            2023-12-15            100          standard   [150.0, 155.0, 160.0, 165.0, 170.0, 175.0, 180...]
            2023-12-18            100           weeklys   [391.0, 392.0, 393.0, 394.0, 395.0, 396.0, 397...]
            2023-12-19            100           weeklys   [391.0, 392.0, 393.0, 394.0, 395.0, 396.0, 397...]
            2023-12-20            100           weeklys   [391.0, 392.0, 393.0, 394.0, 395.0, 396.0, 397...]
            2023-12-21            100           weeklys   [391.0, 392.0, 393.0, 394.0, 395.0, 396.0, 397...]
            2023-12-22            100           weeklys   [285.0, 290.0, 295.0, 300.0, 305.0, 310.0, 315...]
            2023-12-26            100           weeklys   [350.0, 355.0, 360.0, 365.0, 370.0, 375.0, 380...]

        :param symbol: Underlying Stock Symbol to get option expirations for.
        :param strikes: Include strikes in response.
        :param contract_size: Include contract size in response.
        :param expiration_type: Include expiration type in response.
        :param include_all_roots: Get expirations related to all option roots. Default is False.
        :return: List of option expirations.
        """
        # Create payload
        payload = {
            "symbol": symbol,
            "strikes": strikes,
            "contractSize": contract_size,
            "expirationType": expiration_type,
            "includeAllRoots": include_all_roots,
        }

        # Get response
        response = self.request(self.OPTION_EXPIRATIONS_ENDPOINT, payload)

        if not response["expirations"] or "expiration" not in response["expirations"]:
            raise LookupError(f"No Option Expirations found for: Symbol={payload['symbol']}")

        # Parse response
        expirations = response["expirations"]["expiration"]
        expirations = expirations if isinstance(expirations, list) else [expirations]
        df = pd.json_normalize(expirations)

        # Clean up names and set index to be the date (not datetime)
        df = df.rename(columns={"strikes.strike": "strikes"})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df.set_index("date")

    def get_option_chains(self, symbol: str, expiration: Union[dt.date, str], greeks=False) -> pd.DataFrame:
        """
        Get option chains for a symbol and expiration.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/options/get-options-chains

        :param symbol: Underlying Stock Symbol to get option chains for.
        :param expiration: Expiration date to get option chains for.
        :param greeks: Include greeks in response.
        :return: DataFrame of option chains. See Tradier weblink for column definitions. If greeks are requested,
                column names like "greeks.delta" will be included.
        """
        # Create payload
        payload = {
            "symbol": symbol,
            "expiration": self.date2str(expiration),
            "greeks": greeks,
        }

        # Get response
        response = self.request(self.OPTION_CHAIN_ENDPOINT, payload)

        if not response["options"] or "option" not in response["options"]:
            raise LookupError(
                f"No Option Chains found for: Symbol={payload['symbol']}, " f"Expiration={payload['expiration']}"
            )

        # Parse response
        chains = response["options"]["option"]
        chains = chains if isinstance(chains, list) else [chains]
        df = pd.json_normalize(chains)
        df["expiration_date"] = pd.to_datetime(df["expiration_date"]).dt.date
        return df

    def get_option_strikes(self, symbol: str, expiration: Union[dt.date, str]) -> list[float]:
        """
        Get option strikes for a symbol and expiration.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/options/get-options-strikes

        :param symbol: Underlying Stock Symbol to get option strikes for.
        :param expiration: Expiration date to get option strikes for.
        :return: List of option strikes.
        """
        # Create payload
        payload = {
            "symbol": symbol,
            "expiration": self.date2str(expiration),
        }

        # Get response
        response = self.request(self.OPTION_STRIKES_ENDPOINT, payload)

        if not response["strikes"] or "strike" not in response["strikes"]:
            raise LookupError(
                f"No Option Strikes found for: Symbol={payload['symbol']}, " f"Expiration={payload['expiration']}"
            )

        # Parse response
        strikes = response["strikes"]["strike"]
        return strikes if isinstance(strikes, list) else [strikes]

    def get_option_symbol(
        self,
        symbol: str,
        expiration: Union[dt.date, str],
        strike: float,
        option_type: str,
        chains: Union[pd.DataFrame, None] = None,
    ) -> str:
        """
        Get option symbol for a symbol, expiration, strike, and option type.

        This is a convenience function that will call get_option_chains() and return the option symbol. If you want
        more than just the option symbol or more than one option symbol, call get_option_chains() directly.

        :param symbol: Underlying Stock Symbol to get option symbol for.
        :param expiration: Expiration date to get option symbol for.
        :param strike: Strike to get option symbol for.
        :param option_type: Option type to get option symbol for. Valid values are: call, put
        :param chains: DataFrame of option chains. If not provided, will call get_option_chains() to get the chains.
        :return: Option symbol.
        """
        if not isinstance(chains, pd.DataFrame) or chains.empty:
            chains = self.get_option_chains(symbol, expiration)
        symbol = chains.loc[(chains["strike"] == strike) & (chains["option_type"] == option_type.lower())]["symbol"]
        if len(symbol) == 0:
            raise LookupError(
                f"No Option Symbol found for: Symbol={symbol}, Expiration={expiration}, Strike={strike}, "
                f"Option Type={option_type}"
            )

        return symbol.iloc[0]

    def get_clock(self):
        """
        Get the current market clock.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/get-clock

        :return: Dictionary of market clock information. See Tradier weblink for key definitions.
        """
        response = self.request(self.CLOCK_ENDPOINT)
        return response["clock"]

    def get_calendar(self, month: int, year: int) -> pd.DataFrame:
        """
        Get the market calendar for a month and year.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/get-calendar

        :param month: Month to get calendar for.
        :param year: Year to get calendar for.
        :return: DataFrame of market calendar. See Tradier weblink for column definitions.
        """
        # Create payload
        payload = {
            "month": f"{month:02d}",
            "year": str(year),
        }

        # Get response
        response = self.request(self.CALENDAR_ENDPOINT, payload)

        if not response["calendar"] or "days" not in response["calendar"]:
            raise LookupError(f"No Calendar found for: Month={payload['month']}, Year={payload['year']}")

        # Parse response
        calendar = response["calendar"]["days"]["day"]
        calendar = calendar if isinstance(calendar, list) else [calendar]
        df = pd.json_normalize(calendar)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df.set_index("date")

    def lookup_symbol(
        self, query: str, exchanges: Union[str, list, None] = None, types: Union[str, list, None] = None
    ) -> pd.DataFrame:
        """
        Lookup a symbol.

        Documentation: https://documentation.tradier.com/brokerage-api/markets/lookup

        :param query: Query string to lookup.
        :param exchanges: List or Comma separated list of exchanges to lookup. Example: Q,N
        :param types: List or Comma separated list of types to lookup. Valid values are: stock, option etf, index
        :return: DataFrame of symbols. See Tradier weblink for column definitions.
        """
        valid_types = ["stock", "option", "etf", "index"]
        if types:
            if isinstance(types, str):
                types = types.split(",")
            for t in types:
                if t.lower() not in valid_types:
                    raise ValueError(f"Invalid type {t}. Valid types are {valid_types}")

        # Create payload
        payload = {
            "q": query,
        }
        if exchanges:
            payload["exchanges"] = exchanges if isinstance(exchanges, str) else ",".join(exchanges)
        if types:
            payload["types"] = types if isinstance(types, str) else ",".join(types)

        # Get response
        response = self.request(self.LOOKUP_SYMBOL_ENDPOINT, payload)

        if not response["securities"] or "security" not in response["securities"]:
            raise LookupError(
                f"No Symbols found for: Query={payload['q']}, Exchanges={payload['exchanges']}, "
                f"Types={payload['types']}"
            )

        # Parse response
        securities = response["securities"]["security"]
        securities = securities if isinstance(securities, list) else [securities]
        df = pd.json_normalize(securities)
        return df

    def get_previous_trading_day(self, date: Union[dt.datetime, dt.date, str, None] = None) -> dt.date:
        """
        Get the previous trading day.

        :param date: Date to get the previous trading day for. If None, will use today.
        :return: Previous trading day.
        """
        if not date:
            date = dt.date.today()

        # Get calendar for the month of the date
        calendar = self.get_calendar(date.month, date.year)

        # Get the previous trading day
        previous_trading_day = calendar[(calendar["status"] == "open") & (calendar.index < date)].index[-1]

        return previous_trading_day
