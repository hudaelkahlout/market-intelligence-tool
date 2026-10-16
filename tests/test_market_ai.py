from unittest.mock import patch, MagicMock
import json
from market_engine import clean_reviews
from market_ai import prepare_evidence, generate_insights, normalize_response, SECTIONS
import pytest

APPS=[{'app_id':'a','title':'A'},{'app_id':'b','title':'B'}]
ROWS=clean_reviews([{'content':'bad contact x@y.com','score':1},{'content':'good','score':5}],'a')

def test_evidence_filter_budget():
    evidence=prepare_evidence(APPS,ROWS)
    assert len(evidence[0]['reviews'])==1
    assert '[email removed]' in evidence[0]['reviews'][0]['text']
    assert len(json.dumps(prepare_evidence(APPS,ROWS*100),ensure_ascii=False))<24000
    assert prepare_evidence(APPS,ROWS,max_chars=1000)[0]['reviews']==[]

def test_missing_key(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    assert 'GEMINI_API_KEY' in generate_insights(APPS,ROWS)['error']

def test_api_failure_and_normalization():
    with patch('market_ai.genai.Client',side_effect=RuntimeError('secret')):
        result=generate_insights(APPS,ROWS,api_key='fake')
    assert result['data'] is None and 'secret' not in result['error']
    content={key:[' Evidence '] for key in SECTIONS}
    assert normalize_response(json.dumps(content))['market_gaps']==['Evidence']
    client=MagicMock()
    client.__enter__.return_value.models.generate_content.return_value.text=json.dumps(content)
    with patch('market_ai.genai.Client',return_value=client):
        assert generate_insights(APPS,ROWS,api_key='fake')['data']['market_gaps']==['Evidence']
    with pytest.raises(Exception):
        normalize_response('{}')
    assert generate_insights(APPS,[],api_key='fake')['data'] is None

def test_ai_invalid_provider_output():
    client=MagicMock()
    client.__enter__.return_value.models.generate_content.return_value.text='not JSON'
    with patch('market_ai.genai.Client',return_value=client):
        result=generate_insights(APPS,ROWS,api_key='fake')
    assert result['data'] is None and result['error']

@pytest.mark.parametrize('code,fragment',[(400,'structured'),(401,'credentials'),(403,'credentials'),(404,'unavailable'),(429,'quota'),(503,'overloaded')])
def test_actionable_errors(code,fragment):
    from google.genai.errors import APIError
    from market_ai import friendly_error
    error=APIError(code,{'error':{'message':'secret-key-must-never-appear','code':code}})
    message=friendly_error(error)
    assert fragment in message and 'secret-key' not in message

def test_overload_fallback(monkeypatch):
    from google.genai.errors import APIError
    monkeypatch.setenv('GEMINI_FALLBACK_MODEL','gemini-3.5-flash-lite')
    client=MagicMock()
    models=client.__enter__.return_value.models
    response=MagicMock(text=json.dumps({key:['Evidence'] for key in SECTIONS}))
    models.generate_content.side_effect=[APIError(503,{'error':{'code':503,'message':'high demand'}}),response]
    with patch('market_ai.genai.Client',return_value=client) as factory:
        result=generate_insights(APPS,ROWS,api_key='fake',model='gemini-3.8-flash')
    assert result['data'] and result['model_used']=='gemini-3.5-flash-lite'
    assert result['notice'] and models.generate_content.call_count==2
    assert factory.call_args.kwargs['http_options']['retry_options']['attempts']==3

def test_quota_does_not_switch_models():
    from google.genai.errors import APIError
    client=MagicMock()
    models=client.__enter__.return_value.models
    models.generate_content.side_effect=APIError(429,{'error':{'code':429,'message':'quota'}})
    with patch('market_ai.genai.Client',return_value=client):
        result=generate_insights(APPS,ROWS,api_key='fake')
    assert 'quota' in result['error'] and models.generate_content.call_count==1

def test_disabled_fallback(monkeypatch):
    from google.genai.errors import APIError
    monkeypatch.setenv('GEMINI_FALLBACK_MODEL','')
    client=MagicMock()
    models=client.__enter__.return_value.models
    models.generate_content.side_effect=APIError(503,{'error':{'code':503,'message':'busy'}})
    with patch('market_ai.genai.Client',return_value=client):
        result=generate_insights(APPS,ROWS,api_key='fake')
    assert '503' in result['error'] and models.generate_content.call_count==1
