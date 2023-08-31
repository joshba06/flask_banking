def test_home(client):
    landing = client.get("/")
    html = landing.data.decode()
    assert "Main Account" in html
