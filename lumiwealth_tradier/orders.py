import logging
import re
from typing import Union

import pandas as pd

from .base import TradierApiBase, TradierApiError

class OrderLeg:
    def __init__(self, option_symbol: str = None, side: str = None, quantity: int = None, price: float = None, stock_symbol: str = None, stop: float = None, type: str = None):
        """
        Initializes an OrderLeg object with the given parameters.

        :param option_symbol: The OCC option symbol for the leg.
        :param side: The side of the order ('buy_to_open', 'buy_to_close', 'sell_to_open', 'sell_to_close').
        :param quantity: The quantity of the leg.
        :param price: The price for the leg.
        :param stock_symbol: The symbol of the underlying stock for the option.
        :param stop: The stop price for the leg.
        :param type: The type of the order ('market', 'limit', 'stop', 'stop_limit').
        """

        self.option_symbol = option_symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.stock_symbol = stock_symbol
        self.stop = stop
        self.type = type


class Orders(TradierApiBase):
    def __init__(self, account_number, auth_token, is_paper=True):
        TradierApiBase.__init__(self, account_number, auth_token, is_paper)

        # Order endpoint
        self.ORDER_ENDPOINT = f"v1/accounts/{self.ACCOUNT_NUMBER}/orders"  # POST

        # Valid values for checking inputs
        self.valid_durations = ["day", "gtc", "pre", "post"]
        self.valid_order_types = ["market", "limit", "stop", "stop_limit"]

    def cancel(self, order_id: int) -> dict:
        """
        Cancel an existing order.

        Documentation: https://documentation.tradier.com/brokerage-api/trading/cancel-order

        :param order_id: Order ID reported by the order() or order_option() functions
        :return: json object
        """

        try:
            response = self.delete(f"{self.ORDER_ENDPOINT}/{order_id}")
        except TradierApiError as e:
            if "400 - order already in finalized state" in str(e):
                return {"id": order_id, "status": "ok"}
            else:
                raise e
        return response["order"]

    def get_order(self, order_id: Union[int, str], include_tag=True) -> pd.DataFrame:
        """
        Get a specific order based upon the order ID returned by Tradier after submission.

        Documentation: https://documentation.tradier.com/brokerage-api/accounts/get-account-order

        :param order_id:  Order ID reported by the order() or order_option() functions
        :param include_tag:  Include the tag column in the DataFrame. Default is True.
        :return:
        """
        payload = {
            "includeTags": include_tag,
        }
        data = self.request(
            endpoint=f"{self.ORDER_ENDPOINT}/{order_id}", params=payload
        )
        if "order" not in data:
            return pd.DataFrame()

        return pd.json_normalize(data["order"])

    def get_orders(self, include_tag=True) -> pd.DataFrame:
        """
        This function returns a pandas DataFrame.
        Each row denotes a queued order. Each column contiains a feature_variable pertaining to the order.

        Documentation: https://documentation.tradier.com/brokerage-api/accounts/get-account-orders

        Transposed sample output has the following structure:

        >>> tradier_orders = orders(account_number='<id>', auth_token='<token>')
        >>> df_orders = tradier_orders.get_orders()
                                                   0                         1
        id                                   8248093                   8255194
        type                              stop_limit                    market
        symbol                                   UNP                        CF
        side                                     buy                       buy
        quantity                                 3.0                      10.0
        status                                  open                    filled
        duration                                 day                       gtc
        price                                  200.0                       NaN
        avg_fill_price                           0.0                     87.39
        exec_quantity                            0.0                      10.0
        last_fill_price                          0.0                     87.39
        last_fill_quantity                       0.0                      10.0
        remaining_quantity                       3.0                       0.0
        stop_price                             200.0                       NaN
        create_date         2023-09-25T20:29:10.351Z  2023-09-26T14:45:00.155Z
        transaction_date    2023-09-26T12:30:19.152Z  2023-09-26T14:45:00.216Z
        class                                 equity                    equity

        :param include_tag: Include the tag column in the DataFrame. Default is True.
        """
        payload = {
            "includeTags": include_tag,
        }
        data = self.request(endpoint=self.ORDER_ENDPOINT, params=payload)

        # If there are no orders, the API returns an empty dict
        if not data["orders"] or "order" not in data["orders"]:
            return pd.DataFrame()

        return pd.json_normalize(data["orders"]["order"])

    def modify(
        self,
        order_id: int,
        duration: str = "",
        limit_price: Union[float, None] = None,
        stop_price: Union[float, None] = None,
    ) -> dict:
        """
        Modify an existing order. I.e. change the stoploss price. Quantity cannot be changed, only the price or
        duration. To change the quantity, cancel the order and place a new one.

        Documentation: https://documentation.tradier.com/brokerage-api/trading/change-order

        :param order_id: Order ID reported by the order() or order_option() functions
        :param duration: 'day', 'gtc', 'pre', 'post'
        :param limit_price: Limit price. Required for limit and stop_limit orders.
        :param stop_price: Stop price. Required for stop and stop_limit orders.
        :return: json object
        """
        payload = {
            "order_id": order_id,
        }
        if duration:
            if duration.lower() not in self.valid_durations:
                raise ValueError(f"Invalid duration. Must be one of {self.valid_durations}")
            payload["duration"] = duration.lower()
        if limit_price:
            payload["price"] = limit_price
        if stop_price:
            payload["stop"] = stop_price

        response = self.send(f"{self.ORDER_ENDPOINT}/{order_id}", payload, method="put")
        return response["order"]

    def order(
        self,
        symbol: str,
        side: str,
        quantity: Union[int, float],
        order_type: str,
        option_symbol: str = "",
        duration="day",
        limit_price: Union[float, None] = None,
        stop_price: Union[float, None] = None,
        tag: str = "",
        order_class: str = "equity",
    ) -> dict:
        """
        Place an equity order.

        Documentation: https://documentation.tradier.com/brokerage-api/trading/place-equity-order

        :param symbol: Asset symbol (e.g. 'SPY')
        :param side: 'buy', 'sell', 'buy_to_cover', 'sell_short', "buy_to_open", "buy_to_close", "sell_to_open", "sell_to_close"
        :param quantity: Quantity of shares to buy or sell
        :param order_type: 'market', 'limit', 'stop', 'stop_limit'
        :param duration: 'day', 'gtc', 'pre', 'post'
        :param limit_price: Limit price. Required for limit and stop_limit orders.
        :param stop_price: Stop price. Required for stop and stop_limit orders.
        :param tag: Optional tag for the order. Must be letters, numbers and dash (-) characters
        :return: json object
        """
        self._check_order_inputs(duration, limit_price, order_type, stop_price, tag)

        # Equite and Options have different valid sides
        valid_sides = [
            "buy",
            "sell",
            "buy_to_cover",
            "sell_short",
            "buy_to_open",
            "buy_to_close",
            "sell_to_open",
            "sell_to_close",
        ]
        if side.lower() not in valid_sides:
            raise ValueError(f"Invalid side. Must be one of {valid_sides}")
        
        symbol_clean = symbol.upper()
        # If the symbol contains a "." (eg. "BRK.B"), we need to remove it
        if "." in symbol_clean:
            symbol_clean = symbol_clean.replace(".", "/")

        payload = {
            "class": order_class,
            "symbol": symbol_clean,
            "option_symbol": option_symbol.upper(),
            "side": side.lower(),
            "quantity": int(quantity),
            "type": order_type.lower(),
            "duration": duration.lower(),
        }
        self._update_order_payload(payload, limit_price, order_type, stop_price, tag)

        response = self.send(self.ORDER_ENDPOINT, payload)
        return response["order"]

    def order_option(
        self,
        asset_symbol: str,
        option_symbol: str,
        side: str,
        quantity: Union[int, float],
        order_type: str,
        duration="day",
        limit_price: Union[float, None] = None,
        stop_price: Union[float, None] = None,
        tag: str = "",
    ) -> dict:
        """
        Place an option order.

        Documentation: https://documentation.tradier.com/brokerage-api/trading/place-option-order

        :param asset_symbol: Asset symbol (e.g. 'SPY')
        :param option_symbol: OCC option symbol (e.g. 'SPY210416C00300000')
        :param side: 'buy_to_open', 'buy_to_close', 'sell_to_open', 'sell_to_close'
        :param quantity: Quantity of shares to buy or sell
        :param order_type: 'market', 'limit', 'stop', 'stop_limit'
        :param duration: 'day', 'gtc', 'pre', 'post'
        :param limit_price: Limit price. Required for limit and stop_limit orders.
        :param stop_price: Stop price. Required for stop and stop_limit orders.
        :param tag: Optional tag for the order. Must be letters, numbers and dash (-) characters
        :return: json object
        """
        self._check_order_inputs(duration, limit_price, order_type, stop_price, tag)
        valid_sides = ["buy_to_open", "buy_to_close", "sell_to_open", "sell_to_close"]
        if side.lower() not in valid_sides:
            raise ValueError(f"Invalid side. Must be one of {valid_sides}")

        payload = {
            "class": "option",
            "symbol": asset_symbol.upper(),
            "option_symbol": option_symbol.upper(),
            "side": side.lower(),
            "quantity": int(quantity),
            "type": order_type.lower(),
            "duration": duration.lower(),
        }
        payload = self._update_order_payload(
            payload, limit_price, order_type, stop_price, tag
        )

        # Send the request to the Tradier API
        response = self.send(self.ORDER_ENDPOINT, payload, method="post")

        # Return the response
        return response["order"]

    def multileg_order(
        self,
        symbol: str,
        order_type: str,
        duration: str,
        legs: list[OrderLeg],
        price: float = None,
        tag: str = "",
    ) -> dict:
        """
        Place a multi-leg order with the Tradier API.

        :param symbol: The symbol of the underlying asset for the options.
        :param order_type: The type of order ('market', 'debit', 'credit', 'even').
        :param duration: The duration of the order ('day', 'gtc', 'pre', 'post').
        :param legs: A list of OrderLeg objects, each representing one leg of the multi-leg order.
        :param price: The price for the order, required only for 'debit' and 'credit' orders.
        :param tag: An optional tag for the order.
        :return: A dictionary representing the API's response.
        """
        # Ensure there are no more than 4 legs
        if len(legs) > 4:
            raise ValueError("A multi-leg order can have up to 4 legs.")

        # Start constructing the data payload
        data = {
            "class": "multileg",
            "symbol": symbol.upper(),
            "type": order_type.lower(),
            "duration": duration.lower(),
        }

        if price is not None:
            data["price"] = price

        if tag:
            data["tag"] = tag

        # Add the details of each leg to the data payload
        for index, leg in enumerate(legs):
            # Check the validity of the leg data
            if not isinstance(leg, OrderLeg):
                raise ValueError(f"Leg at index {index} is not an OrderLeg object.")

            if leg.side.lower() not in [
                "buy_to_open",
                "buy_to_close",
                "sell_to_open",
                "sell_to_close",
            ]:
                raise ValueError(
                    f"Invalid side for leg at index {index}. Must be one of ['buy_to_open', 'buy_to_close', 'sell_to_open', 'sell_to_close']"
                )

            if not (isinstance(leg.quantity, (int, float))) or leg.quantity <= 0:
                raise ValueError(
                    f"Invalid quantity for leg at index {index}. Must be a positive number. Got {leg.quantity}"
                )

            data[f"option_symbol[{index}]"] = leg.option_symbol.upper()
            data[f"side[{index}]"] = leg.side.lower()
            data[f"quantity[{index}]"] = int(leg.quantity)

        # Send the request to the Tradier API
        response = self.send(self.ORDER_ENDPOINT, data)

        # Return the response
        return response["order"]
    
    def oco_order(
        self,
        duration: str,
        legs: list[OrderLeg],
        tag: str = "",
    ) -> dict:
        """
        Place an OCO (One Cancels Other) order with the Tradier API.

        :param duration: The duration of the order ('day', 'gtc', 'pre', 'post').
        :param legs: A list of OrderLeg objects, each representing one leg of the OCO order.
        :param tag: An optional tag for the order.
        :return: A dictionary representing the API's response.
        """

        # Ensure there are exactly 2 legs
        if len(legs) != 2:
            raise ValueError("An OCO order must have exactly 2 legs.")

        # Start constructing the data payload
        data = {
            "class": "oco",
            "duration": duration.lower(),
        }

        if tag:
            data["tag"] = tag

        # Add the details of each leg to the data payload
        for index, leg in enumerate(legs):
            # Check the validity of the leg data
            if not isinstance(leg, OrderLeg):
                raise ValueError(f"Leg at index {index} is not an OrderLeg object.")

            if leg.side.lower() not in [
                "buy",
                "buy_to_cover",
                "sell",
                "sell_short",
                "buy_to_open",
                "buy_to_close",
                "sell_to_open",
                "sell_to_close",
            ]:
                raise ValueError(
                    f"Invalid side for leg at index {index}. Must be one of ['buy_to_open', 'buy_to_close', 'sell_to_open', 'sell_to_close']"
                )

            if not isinstance(leg.quantity, int) or leg.quantity <= 0:
                raise ValueError(
                    f"Invalid quantity for leg at index {index}. Must be a positive integer."
                )

            data[f"option_symbol[{index}]"] = leg.option_symbol.upper() if leg.option_symbol else None
            data[f"symbol[{index}]"] = leg.stock_symbol.upper() if leg.stock_symbol else None
            data[f"side[{index}]"] = leg.side.lower() if leg.side else None
            data[f"quantity[{index}]"] = int(leg.quantity) if leg.quantity else None
            data[f"price[{index}]"] = leg.price if leg.price else None
            data[f"stop[{index}]"] = leg.stop if leg.stop else None
            data[f"type[{index}]"] = leg.type if leg.type else None

        # Send the request to the Tradier API
        response = self.send(self.ORDER_ENDPOINT, data)

        # Return the response
        return response["order"]

    @staticmethod
    def _update_order_payload(payload, limit_price, order_type, stop_price, tag):
        if order_type.lower() == "limit" or order_type.lower() == "stop_limit":
            payload["price"] = round(limit_price, 2)
        if order_type.lower() == "stop" or order_type.lower() == "stop_limit":
            payload["stop"] = round(stop_price, 2)
        if tag:
            payload["tag"] = tag

        return payload

    def _check_order_inputs(self, duration, limit_price, order_type, stop_price, tag):
        if order_type.lower() not in self.valid_order_types:
            raise ValueError(
                f"Invalid order_type. Must be one of {self.valid_order_types}"
            )
        if duration.lower() not in self.valid_durations:
            raise ValueError(f"Invalid duration. Must be one of {self.valid_durations}")
        if order_type.lower() in ["limit", "stop_limit"] and not limit_price:
            raise ValueError(f"Limit price is required for order_type {order_type}")
        if order_type.lower() in ["stop", "stop_limit"] and not stop_price:
            raise ValueError(f"Stop price is required for order_type {order_type}")
        # Check that 'tag' only has letters, mumbers and dash (-)
        if tag and not re.match(r"^[a-zA-Z0-9-]+$", tag):
            raise ValueError(
                f"Invalid tag {tag}. Must be letters, numbers and dash (-) characters"
            )
