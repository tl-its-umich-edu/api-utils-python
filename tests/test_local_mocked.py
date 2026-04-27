from datetime import datetime
from unittest.mock import Mock

import pytest

from umich_api.api_utils import ApiUtil


def _mock_response(status_code=200, json_data=None, text="", links=None):
    response = Mock()
    response.ok = status_code < 400
    response.status_code = status_code
    response.text = text
    response.links = links or {}
    response.json.return_value = json_data or {}
    return response


@pytest.fixture
def apiutil():
    return ApiUtil("https://example.test", "client-id", "client-secret")


def test_api_call_get_uses_token_and_scope(monkeypatch, apiutil):
    token_response = _mock_response(
        status_code=200,
        json_data={"access_token": "abc123", "expires_in": 3600},
    )
    api_response = _mock_response(status_code=200, text='{"ok": true}')

    post_mock = Mock(return_value=token_response)
    get_mock = Mock(return_value=api_response)
    monkeypatch.setattr("umich_api.api_utils.requests.post", post_mock)
    monkeypatch.setattr("umich_api.api_utils.requests.get", get_mock)

    result = apiutil.api_call("MCommunity/People/uniqname", "mcommunity")

    assert result.status_code == 200
    post_mock.assert_called_once()
    get_mock.assert_called_once()
    call_kwargs = get_mock.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer abc123"


def test_token_is_cached_until_expired(monkeypatch, apiutil):
    token_response = _mock_response(
        status_code=200,
        json_data={"access_token": "cached-token", "expires_in": 3600},
    )
    post_mock = Mock(return_value=token_response)
    monkeypatch.setattr("umich_api.api_utils.requests.post", post_mock)

    token1 = apiutil.get_access_token("oauth2/token", "mcommunity")
    token2 = apiutil.get_access_token("oauth2/token", "mcommunity")

    assert token1 == "cached-token"
    assert token2 == "cached-token"
    assert post_mock.call_count == 1


def test_expire_token_forces_renewal(monkeypatch, apiutil):
    first = _mock_response(
        status_code=200,
        json_data={"access_token": "token-1", "expires_in": 3600},
    )
    second = _mock_response(
        status_code=200,
        json_data={"access_token": "token-2", "expires_in": 3600},
    )
    post_mock = Mock(side_effect=[first, second])
    monkeypatch.setattr("umich_api.api_utils.requests.post", post_mock)

    assert apiutil.get_access_token("oauth2/token", "mcommunity") == "token-1"
    assert apiutil.expire_token(client_scope="mcommunity") is True
    assert apiutil.get_access_token("oauth2/token", "mcommunity") == "token-2"
    assert post_mock.call_count == 2


def test_get_next_page_parses_query_params(apiutil):
    response = _mock_response(
        status_code=200,
        links={
            "next": {
                "url": "https://example.test/resource?page=2&per_page=10",
            }
        },
    )

    next_page = apiutil.get_next_page(response)

    assert next_page == {"page": ["2"], "per_page": ["10"]}


def test_get_next_page_returns_none_without_link(apiutil):
    response = _mock_response(status_code=200, links={})
    assert apiutil.get_next_page(response) is None


def test_unsupported_method_raises(apiutil):
    with pytest.raises(Exception, match="unsupported"):
        apiutil._api_call("resource", "access-token", method="PATCH")


def test_expire_token_returns_false_if_not_cached(apiutil):
    assert apiutil.expire_token(client_scope="mcommunity") is False


def test_get_oauth_token_returns_none_on_error(monkeypatch, apiutil):
    failed_response = _mock_response(status_code=500, text="boom")
    monkeypatch.setattr("umich_api.api_utils.requests.post", Mock(return_value=failed_response))

    token = apiutil.get_oauth_token("oauth2/token", "mcommunity")

    assert token is None


def test_expire_token_sets_expires_time(monkeypatch, apiutil):
    token_response = _mock_response(
        status_code=200,
        json_data={"access_token": "abc123", "expires_in": 3600},
    )
    monkeypatch.setattr("umich_api.api_utils.requests.post", Mock(return_value=token_response))
    apiutil.get_access_token("oauth2/token", "mcommunity")

    assert apiutil.expire_token(client_scope="mcommunity") is True
    token_key = "oauth2/token/mcommunity"
    assert apiutil.tokens[token_key]["expires_time"] <= datetime.now()
