import os

import pytest

from lumiwealth_tradier.base import TradierApiError
from lumiwealth_tradier.tradier import Tradier


@pytest.fixture
def tradier():
    tradier_acct = os.getenv('TRADIER_ACCOUNT_NUMBER')
    tradier_token = os.getenv('TRADIER_PAPER_TOKEN')
    return Tradier(tradier_acct, tradier_token, is_paper=True)


class TestOrders:
    def test_bad_order_inputs(self, tradier):
        with pytest.raises(ValueError):
            tradier.orders.order(symbol='AAPL', quantity=1, side='bad_side', order_type='market', tag='unittest')
        with pytest.raises(ValueError):
            tradier.orders.order(symbol='AAPL', quantity=1, side='buy', order_type='bad_order_type', tag='unittest')
        with pytest.raises(ValueError):
            tradier.orders.order(symbol='AAPL', quantity=1, side='buy', order_type='market', tag='unittest',
                                 duration='bad_duration')
        with pytest.raises(ValueError):
            tradier.orders.order(symbol='AAPL', quantity=1, side='buy', order_type='market', tag='bad tag !@#',
                                 duration='gtc')
        # Missing limit_price
        with pytest.raises(ValueError):
            tradier.orders.order(symbol='AAPL', quantity=1, side='buy', order_type='limit', tag='unittest',
                                 duration='gtc')
        # Missing stop_price
        with pytest.raises(ValueError):
            tradier.orders.order(symbol='AAPL', quantity=1, side='buy', order_type='stop', tag='unittest',
                                 duration='gtc')

    def test_stock_order(self, tradier):
        # Invalid side for stocks
        with pytest.raises(TradierApiError):
            tradier.orders.order(symbol='AAPL', quantity=1, side='buy_to_open', order_type='market', tag='unittest')

        # Submit basic order
        basic_order = tradier.orders.order(symbol='AAPL', quantity=1, side='buy', order_type='market', tag='unittest')
        assert isinstance(basic_order, dict)
        assert 'id' in basic_order.keys()
        assert 'status' in basic_order.keys()
        assert basic_order['id'] > 0

        # Retrieve order status
        order_status = tradier.orders.get_order(basic_order['id'])
        assert 'id' in order_status.columns
        assert order_status['id'].iloc[0] == basic_order['id']

        # Cancel the testing order once we are done
        resp = tradier.orders.cancel(basic_order['id'])
        assert resp
        assert resp['id'] == basic_order['id']

    def test_option_order(self, tradier):
        # Invalid side for options
        with pytest.raises(ValueError):
            tradier.orders.order_option(asset_symbol='AAPL', option_symbol='', quantity=1, side='buy',
                                        order_type='market', tag='unittest')

        # Lookup Expiration Date, Strike, and Option Symbol
        df_expr = tradier.market.get_option_expirations('SPY')
        assert df_expr is not None
        expr_date = df_expr.index[1]
        # Pick a strike from the middle of the list
        strk_idx = int(len(df_expr.iloc[0]['strikes']) / 2)
        strike = df_expr.iloc[0]['strikes'][strk_idx]
        chains_df = tradier.market.get_option_chains('SPY', expr_date)
        assert chains_df is not None
        option_symbol = chains_df[
            (chains_df['strike'] == strike) & (chains_df['option_type'] == 'call')
        ].iloc[0]['symbol']

        # Place the order
        option_order = tradier.orders.order_option(asset_symbol="SPY", option_symbol=option_symbol, quantity=1,
                                                   side='buy_to_open', order_type='market', tag='unittest')
        assert isinstance(option_order, dict)
        assert 'id' in option_order.keys()
        assert 'status' in option_order.keys()
        assert option_order['id'] > 0

        # Cancel the testing order once we are done
        resp = tradier.orders.cancel(option_order['id'])
        assert resp
        assert resp['id'] == option_order['id']
