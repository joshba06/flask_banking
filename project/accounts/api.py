# Flask
from flask import jsonify

# Models
from project.models import Transaction
from project.db import db_session

# Basics
from datetime import datetime




def create(transaction):
    transaction = dict(description=transaction.get("description"),amount=transaction.get("amount"), category=transaction.get("category"), date_booked=transaction.get("date_booked"))

    # Validate request data
    if transaction["description"] == None or len(transaction["description"]) > 80:
        return jsonify({'error': 'Invalid or missing description'}), 400

    if not isinstance(transaction["amount"], (int, float)):
        return jsonify({'error': 'Invalid or missing amount'}), 400

    if transaction["category"] not in ["Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"]:
        return jsonify({'error': 'Invalid category value'}), 400

    if transaction["date_booked"] != None and transaction["date_booked"] != "None":
        try:
            transaction["date_booked"] = datetime.fromisoformat(transaction["date_booked"].replace('Z', '+00:00'))
        except:
            return jsonify({'error': 'Could not convert date_booked to datetime object,'}), 400

    # Create a new Transaction object
    new_transaction = Transaction(**transaction)
    db_session.add(new_transaction)
    db_session.commit()
    new_transaction.calculate_saldo()

    # Return a success response
    return jsonify({
        'id': new_transaction.id,
        'description': new_transaction.description,
        'amount': float(new_transaction.amount),
        'category': new_transaction.category,
        'date_booked': new_transaction.date_booked.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'saldo': float(new_transaction.saldo)
    }), 201
