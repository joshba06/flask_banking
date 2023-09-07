# def test_index_default(client):
#     # Test the default behavior of the route when no filters are applied
#     response = client.get('/')
#     assert response.status_code == 200
#     assert b'None' in response.data  # Check for "None" in the response for empty data


# def test_transactions(client):
#     landing = client.get("/")
#     html = landing.data.decode()
#     assert "Main Account" in html


# Integration tests
# Check if sum of displayed transactions is correct by implementing certain class on document
# Check if number and value of transactions is displayed correctly
