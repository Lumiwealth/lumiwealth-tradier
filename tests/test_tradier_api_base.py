import os
import time
import requests


from lumiwealth_tradier.base import TradierApiBase


class TestTradierApiBase:

    def setup_method(self):
        tradier_acct = os.getenv('TRADIER_ACCOUNT_NUMBER')
        tradier_token = os.getenv('TRADIER_PAPER_TOKEN')
        self.tradier_api_base = TradierApiBase(tradier_acct, tradier_token, is_paper=True)

    def test_retrying_rest_client(self):
        assert self.tradier_api_base is not None

    def test_non_retrying_request_raises_connection_error_quick(self):
        t0 = time.time()
        try:
            response = requests.get(
                'http://localhost:9999',
            )
        except Exception as e:
            pass
        else:
            pass
        finally:
            t1 = time.time()
            actual = t1 - t0
            assert t1 - t0 < 1

    def test_retrying_request_raises_connection_error_slower(self):
        t0 = time.time()
        try:
            response = self.tradier_api_base.requests_retry_session(retries=2).get(
                'http://localhost:9999',
            )
        except Exception as e:
            pass
        else:
            pass
        finally:
            t1 = time.time()
            actual = t1 - t0
            assert t1 - t0 > 5