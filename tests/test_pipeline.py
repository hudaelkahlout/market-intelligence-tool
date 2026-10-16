from unittest.mock import patch
import pytest
from market_engine import sentiment, clean_reviews, scrape_reviews, comparison
from pipeline import analyze

@pytest.mark.parametrize('score,label', [(1,'Negative'),(2,'Negative'),(3,'Neutral'),(4,'Positive'),(5,'Positive')])
def test_sentiment(score,label):
    assert sentiment(score)==label

def test_cleaning():
    raw=[None, {}, {'content':'  hi\n there ', 'score':2, 'at':'bad', 'reviewId':'x'},
         {'content':'hi there','score':2}, {'content':'','score':4}, {'content':'x','score':9}]
    rows=clean_reviews(raw,'a')
    assert len(rows)==1 and rows[0]['review_text']=='hi there'
    assert rows[0]['review_timestamp'] is None

def test_pagination_partial():
    with patch('market_engine.reviews', side_effect=[([{'content':'x'}]*100,'next'), OSError]):
        assert len(scrape_reviews('a'))==100

def test_pipeline_independent(tmp_path):
    from market_engine import ScraperError
    apps=[{'app_id':'a','title':'A'},{'app_id':'b','title':'B'}]
    with patch('pipeline.scrape_reviews', side_effect=[ScraperError('offline'),[{'content':'bad','score':1}]]):
        data=analyze(apps,path=tmp_path/'data.db')
    assert len(data['reviews'])==1 and data['persisted']
    summary=comparison(apps,data['reviews'])
    assert list(summary.review_count)==[0,1]

def test_malformed_rows_are_skipped():
    rows=clean_reviews([
        {'content':'valid','score':2,'at':{'unexpected':'value'},'thumbsUpCount':'bad'},
        {'content':'fraction','score':1.5},
        {'content':None,'score':1},
        {'content':'valid','score':2,'reviewId':'another'},
    ],'a')
    assert len(rows)==1
    assert rows[0]['review_timestamp'] is None
    assert rows[0]['thumbs_up']==0

def test_database_failure_preserves_analysis(tmp_path):
    import sqlite3
    apps=[{'app_id':'a','title':'A'},{'app_id':'b','title':'B'}]
    with patch('pipeline.scrape_reviews',return_value=[{'content':'feedback','score':3}]), patch('pipeline.save_data',side_effect=sqlite3.OperationalError):
        data=analyze(apps,path=tmp_path/'data.db')
    assert len(data['reviews'])==2 and not data['persisted']
    assert 'Database' in data['warnings'][-1]

def test_selection_limits_and_review_target():
    from market_engine import validate_selection
    validate_selection([{'app_id':str(i)} for i in range(4)])
    with pytest.raises(ValueError):
        validate_selection([{'app_id':str(i)} for i in range(5)])
    with pytest.raises(ValueError):
        scrape_reviews('a',count=149)
    with pytest.raises(ValueError):
        scrape_reviews('a',count=301)
