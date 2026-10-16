from dashboard import build_charts
import pytest

@pytest.mark.parametrize('n',[2,3,4])
def test_chart_empty_competitors(n):
    charts=build_charts([{'app_id':str(i),'title':str(i),'rating':4} for i in range(n)],[])
    assert len(charts)==4
    assert list(charts[0].layout.yaxis.range)==[0,5]
    assert list(charts[-1].layout.yaxis.range)==[0,1]

def test_missing_metadata_charts():
    charts=build_charts([{'app_id':'a','title':'A','rating':None},{'app_id':'b','title':'B','rating':None}],[])
    assert len(charts)==4
