from database import initialize, save_data, load_data
from market_engine import clean_reviews

def test_database_roundtrip(tmp_path):
    path=tmp_path/'nested'/'data.db'
    initialize(path)
    apps=[{'app_id':'a','title':'A','rating':4.2}]
    rows=clean_reviews([{'reviewId':'r','content':'bad','score':1}],'a')
    save_data(apps,rows,path)
    save_data([dict(apps[0], title='Updated')],rows,path)
    stored,reviews=load_data(['a'],path)
    assert stored[0]['title']=='Updated' and len(reviews)==1
    rows=clean_reviews([{'reviewId':'r','content':'improved','score':4}],'a')
    save_data(apps,rows,path)
    assert load_data(['a'],path)[1][0]['score']==4
    assert load_data([],path)==([],[])

def test_review_local_id_survives_update(tmp_path):
    path=tmp_path/'data.db'
    apps=[{'app_id':'a','title':'A'}]
    save_data(apps,clean_reviews([{'reviewId':'r','content':'old','score':1}, {'reviewId':'s','content':'other','score':3}],'a'),path)
    before={r['review_id']:r['id'] for r in load_data(['a'],path)[1]}
    save_data(apps,clean_reviews([{'reviewId':'r','content':'new','score':4}],'a'),path)
    after={r['review_id']:r['id'] for r in load_data(['a'],path)[1]}
    assert before==after
