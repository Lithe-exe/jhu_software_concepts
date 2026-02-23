import pytest
import app as app_module # Correct import

@pytest.mark.buttons
def test_busy_gating_update_analysis(client):
    # Set the flag on the SAME module instance the app uses
    app_module.IS_BUSY = True
    try:
        res = client.post("/update-analysis")
        assert res.status_code == 409
        assert res.json == {"busy": True}
    finally:
        # Reset to avoid breaking other tests
        app_module.IS_BUSY = False

@pytest.mark.buttons
def test_update_analysis(client):
    app_module.IS_BUSY = False
    res = client.post("/update-analysis")
    assert res.status_code == 200
    assert res.json == {"ok": True}