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
        strike = df_expr.iloc[1]['strikes'][strk_idx]
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

    def test_option_order_multileg(self, tradier):
        from lumiwealth_tradier.orders import OrderLeg

        # Lookup Expiration Date, Strike, and Option Symbol
        df_expr = tradier.market.get_option_expirations('SPY')
        assert df_expr is not None
        expr_date = df_expr.index[1]

        # Pick a strike from the middle of the list
        strk_idx = int(len(df_expr.iloc[1]['strikes']) / 2)
        strike = df_expr.iloc[1]['strikes'][strk_idx]
        chains_df = tradier.market.get_option_chains('SPY', expr_date)
        assert chains_df is not None

        option_symbol_1 = chains_df[
            (chains_df['strike'] == strike) & (chains_df['option_type'] == 'call')
        ].iloc[0]['symbol']

        option_symbol_2 = chains_df[
            (chains_df['strike'] == strike) & (chains_df['option_type'] == 'put')
        ].iloc[0]['symbol']

        # Create multileg order legs
        leg1 = OrderLeg(option_symbol=option_symbol_1, quantity=1, side='buy_to_open')
        leg2 = OrderLeg(option_symbol=option_symbol_2, quantity=1, side='buy_to_open')

        # Example assuming order_type and duration are required and correctly set
        multileg_order = tradier.orders.multileg_order(
            symbol='SPY',
            order_type='market',  # or 'debit', 'credit', 'even', based on your requirement
            duration='day',  # or 'gtc', 'pre', 'post'
            legs=[leg1, leg2],
            price=None,  # Assuming market order for the example
            tag='unittest'
        )
        
        # Check that status is ok
        assert multileg_order['status'] == 'ok'

        # Check it returned id
        assert 'id' in multileg_order

        # Check it returned a partner_id
        assert 'partner_id' in multileg_order

        # Cancel the testing order once we are done
        resp = tradier.orders.cancel(multileg_order['id'])
        assert resp
        assert resp['id'] == multileg_order['id']

    # Test options order multileg with credit price
    def test_option_order_multileg_credit(self, tradier):
        from lumiwealth_tradier.orders import OrderLeg

        # Lookup Expiration Date, Strike, and Option Symbol
        df_expr = tradier.market.get_option_expirations('SPY')
        assert df_expr is not None
        expr_date = df_expr.index[1]

        # Pick a strike from the middle of the list
        strk_idx = int(len(df_expr.iloc[1]['strikes']) / 2)
        strike = df_expr.iloc[1]['strikes'][strk_idx]
        chains_df = tradier.market.get_option_chains('SPY', expr_date)
        assert chains_df is not None

        option_symbol_1 = chains_df[
            (chains_df['strike'] == strike) & (chains_df['option_type'] == 'call')
        ].iloc[0]['symbol']

        option_symbol_2 = chains_df[
            (chains_df['strike'] == strike) & (chains_df['option_type'] == 'put')
        ].iloc[0]['symbol']

        # Create multileg order legs
        leg1 = OrderLeg(option_symbol=option_symbol_1, quantity=1, side='buy_to_open')
        leg2 = OrderLeg(option_symbol=option_symbol_2, quantity=1, side='buy_to_open')

        # Example assuming order_type and duration are required and correctly set
        multileg_order = tradier.orders.multileg_order(
            symbol='SPY',
            order_type="credit",
            duration='day',  # or 'gtc', 'pre', 'post'
            legs=[leg1, leg2],
            price=0.01,  # Limit price
            tag='unittest'
        )
        
        # Check that status is ok
        assert multileg_order['status'] == 'ok'

        # Check it returned id
        assert 'id' in multileg_order.keys()

        # Check it returned a partner_id
        assert 'partner_id' in multileg_order.keys()

        # Cancel the testing order once we are done
        resp = tradier.orders.cancel(multileg_order['id'])
        assert resp
        assert resp['id'] == multileg_order['id']

    def test_buying_brk_stock(self, tradier):
        # Submit basic order
        basic_order = tradier.orders.order(symbol='BRK.B', quantity=1, side='buy', order_type='market', tag='unittest')
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

    def test_buying_spx_index_option(self, tradier):
        # Lookup Expiration Date, Strike, and Option Symbol
        df_expr = tradier.market.get_option_expirations('SPX')
        assert df_expr is not None
        expr_date = df_expr.index[1]
        # Pick a strike from the middle of the list
        strk_idx = int(len(df_expr.iloc[0]['strikes']) / 2)
        strike = df_expr.iloc[0]['strikes'][strk_idx]
        chains_df = tradier.market.get_option_chains('SPX', expr_date)
        assert chains_df is not None
        option_symbol = chains_df[
            (chains_df['strike'] == strike) & (chains_df['option_type'] == 'call')
        ].iloc[0]['symbol']

        # Place the order
        option_order = tradier.orders.order_option(asset_symbol="SPX", option_symbol=option_symbol, quantity=1,
                                                   side='buy_to_open', order_type='market', tag='unittest')
        assert isinstance(option_order, dict)
        assert 'id' in option_order.keys()
        assert 'status' in option_order.keys()
        assert option_order['id'] > 0

        # Cancel the testing order once we are done
        resp = tradier.orders.cancel(option_order['id'])
        assert resp
        assert resp['id'] == option_order['id']
