import threading
from unittest.mock import patch

import requests.sessions

from lumiwealth_tradier.base import TradierApiBase


def test_requests_retry_session_default_does_not_mutate_adapters_during_iteration():
    api = TradierApiBase("test_account", "test_token", is_paper=True)
    session = api._session

    started = threading.Event()
    resume = threading.Event()
    errors: list[Exception] = []

    def iterate_adapters():
        try:
            iterator = iter(session.adapters.items())
            next(iterator)  # Start iteration to create an active iterator
            started.set()
            resume.wait(timeout=2.0)
            for _ in iterator:
                pass
        except Exception as e:  # pragma: no cover - only executes on failure
            errors.append(e)

    t = threading.Thread(target=iterate_adapters)
    t.start()

    assert started.wait(timeout=2.0)

    # This used to remount adapters on the shared session which can raise:
    # RuntimeError: OrderedDict mutated during iteration
    api.requests_retry_session()

    resume.set()
    t.join(timeout=2.0)

    assert errors == []


def test_requests_retry_session_default_is_idempotent_no_mount_calls():
    api = TradierApiBase("test_account", "test_token", is_paper=True)

    with patch.object(requests.sessions.Session, "mount", side_effect=AssertionError("mount called")):
        for _ in range(1000):
            assert api.requests_retry_session() is api._session


def test_requests_retry_session_non_default_returns_new_configured_session():
    api = TradierApiBase("test_account", "test_token", is_paper=True)
    session = api.requests_retry_session(retries=1)

    assert session is not api._session

    adapter = session.get_adapter("https://example.com")
    assert adapter.max_retries.total == 1
