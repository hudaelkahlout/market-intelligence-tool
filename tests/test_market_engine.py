from unittest.mock import patch
import pytest
from market_engine import search_apps, validate_selection, ScraperError

def test_search_normalization():
    with patch('market_engine.search', return_value=[{}, None, {'appId':'a','title':'App'}]):
        assert search_apps('food')[0]['developer'] == 'Unknown developer'
    assert search_apps(' ') == []

def test_selection_and_failure():
    validate_selection([{'app_id':'a'},{'app_id':'b'}])
    with pytest.raises(ValueError):
        validate_selection([{'app_id':'a'}])
    with patch('market_engine.search', side_effect=OSError), pytest.raises(ScraperError):
        search_apps('food')

def test_search_malformed_metadata():
    with patch('market_engine.search',return_value=[{'appId':'x','score':['bad']},{'appId':'y','score':float('inf')} ]):
        assert all(app['rating'] is None for app in search_apps('apps'))

def test_transport_uses_verified_tls():
    import ssl
    from market_engine import _verified_urlopen
    with patch('market_engine.urlopen') as opener:
        _verified_urlopen('https://example.com')
        assert opener.call_args.kwargs['timeout']==20
        assert opener.call_args.kwargs['context'].verify_mode==ssl.CERT_REQUIRED
