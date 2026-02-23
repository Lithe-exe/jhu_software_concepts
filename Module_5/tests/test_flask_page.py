import pytest
@pytest.mark.web
def test_analysis_page(client):
    res = client.get("/analysis")
    assert res.status_code == 200
    assert b"Analysis" in res.data
    assert b"Pull Data" in res.data
    assert b"Update Analysis" in res.data
