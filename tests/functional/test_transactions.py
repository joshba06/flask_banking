def test_transactions(client):
    landing = client.get("/")
    html = landing.data.decode()
    assert "Main Account" in html
