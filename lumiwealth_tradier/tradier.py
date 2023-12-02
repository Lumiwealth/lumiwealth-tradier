from .account import Account
from .equity_order import EquityOrder
from .options_data import OptionsData
from .options_order import OptionsOrder
from .quotes import Quotes


class Tradier:
    def __init__(self, account_number, auth_token, is_paper=True):
        # Define account credentials
        self.is_paper = is_paper
        self.ACCOUNT_NUMBER = account_number
        self.AUTH_TOKEN = auth_token

        self.account = Account(self.ACCOUNT_NUMBER, self.AUTH_TOKEN, is_paper)
        self.equity_order = EquityOrder(self.ACCOUNT_NUMBER, self.AUTH_TOKEN, is_paper)
        self.options_data = OptionsData(self.ACCOUNT_NUMBER, self.AUTH_TOKEN, is_paper)
        self.options_order = OptionsOrder(self.ACCOUNT_NUMBER, self.AUTH_TOKEN, is_paper)
        self.quotes = Quotes(self.ACCOUNT_NUMBER, self.AUTH_TOKEN, is_paper)
