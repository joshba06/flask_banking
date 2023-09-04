import pytest
from project.db import db_session
from datetime import datetime
from project.models import Transaction
from pprint import pprint
import json


# Test data for creating a transaction
BASE_URL = "/flask_banking/api"

valid_transaction_data = {
    "description": "Grocery shopping",
    "amount": 50.00,
    "category": "Groceries",
    "date_booked": "2023-09-04T12:00:00Z"
}

invalid_transaction_data = {
    "description": "Invalid transaction",  # Missing 'amount' and 'category'
    "date_booked": "2023-09-04T12:00:00Z"
}

# Fixture only needed for tests in this module
@pytest.fixture
def sample_transactions():
    transactions = [
        Transaction("Transaction 1", 50.00, "Salary", date_booked=datetime(2023,8,15,15,0,0)),
        Transaction("Transaction 2", -100.00, "Rent", date_booked=datetime(2023,8,15,12,0,0)),
        Transaction("Transaction 3", 300.00, "Salary", date_booked=datetime(2023,8,15,10,0,0))
    ]
    db_session.add_all(transactions)
    db_session.commit()

    return transactions

def clean_up_bytes_string(bytes_string):
    # Decode the bytes string to a regular string
    text_string = bytes_string.decode('utf-8')

    # Remove leading and trailing whitespace and newlines
    text_string = text_string.strip()

    # Load the JSON data from the cleaned-up string
    try:
        json_data = json.loads(text_string)
    except json.JSONDecodeError:
        # Handle JSON decoding errors if needed
        raise ValueError("Invalid JSON data")

    # Return the cleaned-up JSON data
    return json_data

def test_read_all(client, sample_transactions):
    response = client.get(f"{BASE_URL}/transactions")
    assert response.status_code == 200
    data_json = clean_up_bytes_string(response.data)
    assert len(data_json) == 3
    assert Transaction.query.get(data_json[0]["id"]).description == data_json[0]["description"]
    assert str(Transaction.query.get(data_json[0]["id"]).amount) == data_json[0]["amount"]
    assert Transaction.query.get(data_json[0]["id"]).category == data_json[0]["category"]
    assert Transaction.query.get(data_json[0]["id"]).date_booked.isoformat() == data_json[0]["date_booked"]
    
# Test case for creating a transaction with valid data
def test_create_valid_transaction(client):
    response = client.post(f"{BASE_URL}/transactions", json=valid_transaction_data)
    assert response.status_code == 201

# Test case for creating a transaction with invalid data
def test_create_invalid_transaction(client):
    response = client.post(f"{BASE_URL}/transactions", json=invalid_transaction_data)
    assert response.status_code == 400

# Test case for retrieving a single transaction by ID (valid ID)
def test_get_single_transaction(client, sample_transactions):
    # Assuming there is a transaction with ID 1 in the database
    response = client.get(f"{BASE_URL}/transactions/1")
    assert response.status_code == 200

# Test case for retrieving a single transaction by ID (non-existent ID)
def test_get_nonexistent_transaction(client, sample_transactions):
    # Assuming there is no transaction with ID 999 in the database
    response = client.get(f"{BASE_URL}/transactions/999")
    assert response.status_code == 404
