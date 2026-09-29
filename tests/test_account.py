import os

import pandas as pd
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

    def test_get_history_handles_null_payload(self, tradier, monkeypatch):
        monkeypatch.setattr(tradier.account, "request", lambda **_kwargs: {"history": "null"})
        df = tradier.account.get_history()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_history_normalizes_single_event_object(self, tradier, monkeypatch):
        monkeypatch.setattr(
            tradier.account,
            "request",
            lambda **_kwargs: {
                "history": {
                    "event": {
                        "id": "evt-1",
                        "type": "ach",
                        "date": "2026-03-27",
                        "amount": "100.00",
                    }
                }
            },
        )
        df = tradier.account.get_history()
        assert isinstance(df, pd.DataFrame)
        assert len(df.index) == 1
        assert df.iloc[0]["id"] == "evt-1"
