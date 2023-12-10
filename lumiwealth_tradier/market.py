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
        self.SEARCH_ENDPOINT = "v1/markets/search"  # Companies lookup

    # Create functions for each endpoint
    def get_quotes(self, symbols: str | list[str], greeks=False) -> pd.DataFrame:
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
        :return: DataFrame of quotes.
        """
        # Create payload
        symbols = symbols if isinstance(symbols, str) else ','.join(symbols)
        payload = {
            'symbols': ','.join(symbols),
            greeks: greeks
        }

        # Get response
        response = self.request(self.QUOTES_ENDPOINT, payload)

        # Parse response - single Symbol doesn't return a list from the API, multiple symbols do
        quotes = response['quotes']['quote']
        quotes = quotes if isinstance(quotes, list) else [quotes]
        df = pd.DataFrame(quotes)

        return df.set_index('symbol')
