from .base import TradierApiBase


class EquityOrder(TradierApiBase):
    def __init__(self, account_number, auth_token, is_paper=True):
        TradierApiBase.__init__(self, account_number, auth_token, is_paper)

        # Order endpoint
        self.ORDER_ENDPOINT = f"v1/accounts/{self.ACCOUNT_NUMBER}/orders"  # POST

    def order(self, symbol, side, quantity, order_type, duration='day', limit_price=False, stop_price=False):
        """
        Arguments:
            symbol       = Stock Ticker Symbol.
            side       = ['buy', 'buy_to_cover', 'sell', 'sell_short']
            order_type    = ['market', 'limit', 'stop', 'stop_limit']
            duration    = ['day', 'gtc', 'pre', 'post']

         Example of how to run:
            >>> eo = EquityOrder('ACCOUNT_NUMBER', 'AUTH_TOKEN')
            >>> eo.order(symbol='QQQ', side='buy', quantity=10, order_type='market', duration='gtc')
            {'order': {'id': 8256590, 'status': 'ok', 'partner_id': '3a8bbee1-5184-4ffe-8a0c-294fbad1aee9'}}
      """
        # Define initial requests parameters dictionary whose fields are applicable to all order_type values
        params = {
            'class': 'equity',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'type': order_type,
            'duration': duration
        }

        # If the order_type is limit, stop, or stop_limit --> Set the appropriate limit price or stop price
        if order_type.lower() in ['limit', 'stop_limit']:
            params['price'] = limit_price
        if order_type.lower() in ['stop', 'stop_limit']:
            params['stop'] = stop_price

        data = self.send(self.ORDER_ENDPOINT, data=params)
        return data
