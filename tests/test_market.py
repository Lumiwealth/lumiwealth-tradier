import datetime as dt
import os
import re

import pytest

from lumiwealth_tradier.tradier import Tradier


@pytest.fixture
def tradier():
    tradier_acct = os.getenv('TRADIER_ACCOUNT_NUMBER')
    tradier_token = os.getenv('TRADIER_PAPER_TOKEN')
    return Tradier(tradier_acct, tradier_token, is_paper=True)


class TestMarket:
    def test_quote(self, tradier):
        df = tradier.market.get_quotes(['AAPL', 'MSFT', 'bad_symbol'])
        assert df is not None
        assert 'last' in df.columns
        assert df.loc['AAPL']['last'] > 0
        assert df.loc['MSFT']['last'] > 0
        assert 'bad_symbol' not in df.index

        with pytest.raises(ValueError):
            tradier.market.get_last_price('bad_symbol')

        assert tradier.market.get_last_price('AAPL') > 0

    def test_historical_quote(self, tradier):
        # Multiple row return
        df = tradier.market.get_historical_quotes('SPY', start_date='2023-12-01', end_date='2023-12-07')
        assert df is not None
        assert 'open' in df.columns
        assert df.iloc[0]['open'] > 0

        # Single row return
        df = tradier.market.get_historical_quotes('SPY', start_date='2023-12-01', end_date='2023-12-01')
        assert df is not None
        assert 'open' in df.columns
        assert df.iloc[0]['open'] > 0

        # Error Check Inputs
        with pytest.raises(ValueError):
            tradier.market.get_historical_quotes('SPY', start_date='2023-12-01', interval='bad_interval')
        with pytest.raises(ValueError):
            tradier.market.get_historical_quotes('SPY', start_date='2023-12-01', session_filter='bad_session_filter')

    def test_timesales(self, tradier, mocker):
        # Error test valid values
        with pytest.raises(ValueError):
            tradier.market.get_timesales('SPY', start_date='2023-12-01', end_date='2023-12-07', interval='bad_interval')
        with pytest.raises(ValueError):
            tradier.market.get_timesales('SPY', start_date='2023-12-01', end_date='2023-12-07',
                                         session_filter='bad_session_filter')

        today = dt.date.today()
        recent_date = tradier.market.get_previous_trading_day(today)
        start_date = dt.datetime.combine(recent_date, dt.time(9, 30))
        end_date = dt.datetime.combine(recent_date, dt.time(9, 45))
        df = tradier.market.get_timesales('SPY', start_date=start_date, end_date=end_date)
        assert len(df)
        assert 'price' in df.columns
        assert df.iloc[0]['price'] > 0

        mocker.patch.object(tradier.market, 'request', return_value={'series': 'null'})
        with pytest.raises(LookupError):
            tradier.market.get_timesales('SPY', start_date=start_date, end_date=end_date)

    def test_option_expirations(self, tradier):
        df = tradier.market.get_option_expirations('SPY', include_all_roots=True)
        assert df is not None
        assert len(df) > 0
        assert 'strikes' in df.columns
        assert isinstance(df.iloc[0]['strikes'], list)
        assert isinstance(df.iloc[0]['strikes'][0], float)

        with pytest.raises(LookupError):
            tradier.market.get_option_expirations('bad_symbol')

    def test_option_chains(self, tradier):
        # Need a valid options date ... so look one up from the expirations
        df_expr = tradier.market.get_option_expirations('SPY')
        assert df_expr is not None
        expr_date = df_expr.index[0]

        # Get the option chains
        df = tradier.market.get_option_chains('SPY', expr_date)
        assert df is not None
        assert len(df) > 0
        assert 'strike' in df.columns
        assert df.iloc[0]['strike'] > 0

        with pytest.raises(LookupError):
            tradier.market.get_option_chains('bad_symbol', '2023-12-01')

    def test_get_option_strikes(self, tradier):
        # Need a valid options date ... so look one up from the expirations
        df_expr = tradier.market.get_option_expirations('SPY')
        assert df_expr is not None
        expr_date = df_expr.index[0]

        # Get the option strikes
        strikes = tradier.market.get_option_strikes('SPY', expr_date)
        assert strikes is not None
        assert isinstance(strikes, list)
        assert len(strikes) > 0
        assert strikes[0] > 0

        with pytest.raises(LookupError):
            tradier.market.get_option_strikes('bad_symbol', '2023-12-01')

    def test_get_option_symbol(self, tradier):
        # Need a valid options date ... so look one up from the expirations
        df_expr = tradier.market.get_option_expirations('SPY')
        assert df_expr is not None
        expr_date = df_expr.index[0]
        strike = df_expr.iloc[0]['strikes'][0]

        # Get the option symbols - lookup chains
        symbol = tradier.market.get_option_symbol('SPY', expr_date, strike, 'call')
        assert symbol is not None
        assert isinstance(symbol, str)
        assert symbol != ''
        assert re.match(r'SPY\d+C\d+', symbol)

        # Pass chains in so additional lookups aren't required
        chains_df = tradier.market.get_option_chains('SPY', expr_date)
        assert chains_df is not None
        symbol = tradier.market.get_option_symbol('SPY', expr_date, strike, 'put', chains_df)
        assert symbol != ''
        assert re.match(r'SPY\d+P\d+', symbol)

        # Unkown Strike
        with pytest.raises(LookupError):
            tradier.market.get_option_symbol('SPY', expr_date, 1000000.99, 'call')

        with pytest.raises(LookupError):
            tradier.market.get_option_symbol('bad_symbol', '2023-12-01', 100, 'call')

    def test_get_clock(self, tradier):
        data = tradier.market.get_clock()
        assert data is not None
        assert 'state' in data
        assert data['state'] in ['open', 'closed', 'premarket', 'postmarket']

    def test_get_calendar(self, tradier):
        df = tradier.market.get_calendar(11, 2023)
        assert df is not None
        assert 'status' in df.columns
        assert df.iloc[0]['status'] in ['open', 'closed']

    def test_lookup_symbol(self, tradier):
        df = tradier.market.lookup_symbol('SPY')
        assert df is not None
        assert 'symbol' in df.columns
        assert df.iloc[0]['symbol'] == 'SPY'

        with pytest.raises(LookupError):
            tradier.market.lookup_symbol('bad_symbol')

    def test_get_previous_trading_day(self, tradier):
        today = dt.date.today()
        trading_day = tradier.market.get_previous_trading_day()
        assert isinstance(trading_day, dt.date)
        assert trading_day < today
        assert trading_day.weekday() < 5
        assert trading_day > today - dt.timedelta(days=7)

        assert tradier.market.get_previous_trading_day(today) == trading_day
