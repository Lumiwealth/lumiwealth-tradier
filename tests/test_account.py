import os

import pytest

from lumiwealth_tradier.tradier import Tradier


@pytest.fixture
def tradier():
    tradier_acct = os.getenv('TRADIER_ACCOUNT_NUMBER')
    tradier_token = os.getenv('TRADIER_PAPER_TOKEN')
    return Tradier(tradier_acct, tradier_token, is_paper=True)


class TestAccount:
    def test_profile(self, tradier):
        df = tradier.account.get_user_profile()
        assert df is not None
        assert 'account.classification' in df.columns

    def test_account_balance(self, tradier):
        df = tradier.account.get_account_balance()
        assert df is not None
        assert 'total_cash' in df.columns
