import pytest
from project.models import Transaction

def test_valid_integer():
    response = Transaction.create("First", 42)
    assert response is None
    assert Transaction.query.count() == 1

def test_valid_float():
    response = Transaction.create("First", 3.14)
    assert response is None
    assert Transaction.query.count() == 1

def test_invalid_string():
    with pytest.raises(ValueError, match="The 'amount' variable must be a decimal, integer or float."):
        Transaction.create("First", "invalid")
    assert Transaction.query.count() == 0

# Test title too long
# Test no title or no amount

# Test adding multiple transactions (implement that dates must be provided too) and if get_all() with filter settings works
# Test the same for group_by
# Check that the saldo is correct



# Integration tests
# Check if sum of displayed transactions is correct by implementing certain class on document
# Check if number and value of transactions is displayed correctly

