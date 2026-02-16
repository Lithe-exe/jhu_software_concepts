import pytest
import src.app as app_module # Import app directly for global flag

@pytest.mark.buttons
def test_busy_gating_update_analysis(client):
    import src.app as app_module
    app_module.IS_BUSY = True
    try:
        res = client.post("/update-analysis")
        assert res.status_code == 409
        assert res.json == {"busy": True}
    finally:
        app_module.IS_BUSY = False

@pytest.mark.buttons
def test_update_analysis(client):
    res = client.post("/update-analysis")
    assert res.status_code == 200
    assert res.json == {"ok": True}
