from unittest.mock import patch
from pathlib import Path

APP_PATH=Path(__file__).resolve().parents[1]/'app.py'
from streamlit.testing.v1 import AppTest
from market_engine import clean_reviews

APPS=[{'app_id':'a','title':'Alpha','developer':'Dev','rating':4,'icon_url':'','play_url':'https://play.google.com/store/apps/details?id=a'},
      {'app_id':'b','title':'Beta','developer':'Dev','rating':3,'icon_url':'','play_url':'https://play.google.com/store/apps/details?id=b'}]

def test_fresh_start():
    at=AppTest.from_file(APP_PATH,default_timeout=20).run()
    assert not at.exception
    assert at.title[0].value.startswith('Market Intelligence')

def test_ui_journey(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    from pathlib import Path
    app_path=str(Path(__file__).resolve().parents[1]/'app.py')
    at=AppTest.from_file(app_path,default_timeout=20).run()
    with patch('market_engine.search_apps',return_value=APPS):
        at.text_input[0].set_value('food delivery')
        at.button[0].click().run()
    assert not at.exception
    assert at.button[-1].disabled
    at.multiselect[0].set_value(['a','b']).run()
    with patch('pipeline.scrape_reviews',return_value=[{'content':'Crashes when opening','score':1},{'content':'Helpful app','score':5}]):
        next(b for b in at.button if b.label=='Analyze competitors').click().run()
    assert not at.exception
    assert len(at.session_state['analysis']['reviews'])==4
    assert at.session_state['report'][:2]==b'PK'
    with patch('pipeline.scrape_reviews',side_effect=AssertionError('Unexpected scrape')):
        at.selectbox[0].select('All competitors').run()
    assert not at.exception

def test_search_error_has_friendly_state():
    from market_engine import ScraperError
    at=AppTest.from_file(APP_PATH,default_timeout=20).run()
    with patch('market_engine.search_apps',side_effect=ScraperError('Search unavailable; retry shortly.')):
        at.text_input[0].set_value('food delivery')
        at.button[0].click().run()
    assert not at.exception
    assert 'unavailable' in at.error[0].value
