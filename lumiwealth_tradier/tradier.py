from .account import Account
from .market import MarketData
from .orders import Orders


class Tradier:
    def __init__(self, account_number, auth_token, is_paper=True):
        # Define account credentials
        self.is_paper = is_paper
        self.ACCOUNT_NUMBER = account_number
        self.AUTH_TOKEN = auth_token

        self.account = Account(self.ACCOUNT_NUMBER, self.AUTH_TOKEN, is_paper)
        self.orders = Orders(self.ACCOUNT_NUMBER, self.AUTH_TOKEN, is_paper)
        self.market = MarketData(self.ACCOUNT_NUMBER, self.AUTH_TOKEN, is_paper)
