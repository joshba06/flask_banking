# Flask
from flask import jsonify

# Models
from project.models import Account
from project.accounts.accounts import create_account, generate_unique_iban
from project.db import db_session


def accounts_to_json(accounts_list):
    json_accounts = []
    for account in accounts_list:
        account_dict = {
            "id": str(account.id),
            "title": str(account.title),
            "iban": str(account.iban),
        }
        json_accounts.append(account_dict)
    return json_accounts

def api_get_one_account(id):

    if not id:
        return jsonify({"status": "error", "detail": "This was unexpected. Swagger should have handled this..."}), 400

    account = Account.query.get(id)
    if not account:
        return jsonify({
            "detail": "Account not found.",
            "status": "error"}), 404
    else:
        return accounts_to_json([account])

def api_get_all_accounts():

    accounts = Account.query.all()
    if len(accounts) == 0 or not accounts:
        return jsonify({
            "detail": "No accounts found.",
            "status": "error"}), 404
    else:
        return accounts_to_json(accounts)

def api_create_account(account):

    # Title validation (existence, length, type) and error messages are automatically generated by swagger!
    title = account.get('title')
    if not title:
        return jsonify({"status": "error", "message": "This was unexpected. Swagger should have handled this..."}), 400

    new_iban = generate_unique_iban()

    status, message = create_account(new_iban, title) # Validates request data internally (given it is not None)

    if status == "success":
        account = Account.query.filter(Account.iban == new_iban).first()
        return jsonify({
                "status": "success",
                "detail": message,
                "iban": account.iban,
                "title": account.title,
                "id": account.id
            }), 201
    else:
        return jsonify({"status": "error", "detail": message}), 400

def api_delete_account(id):

    if not id:
        return jsonify({"status": "error", "detail": "This was unexpected. Swagger should have handled this..."}), 400

    account_to_delete = Account.query.get(id)
    if not account_to_delete:
        return jsonify({"detail": "Account not found.", "status": "error"}), 404

    if Account.query.limit(2).count() <= 1:
        return jsonify({"detail": "Cannot delete the last account.", "status": "error"}), 400

    try:
        db_session.delete(account_to_delete)
        db_session.commit()

        next_account_id = Account.query.first().id
        return jsonify({
            "detail": "Successfully deleted account.",
            "status": "success"
        }), 200

    except Exception as e:  # Keep this for unexpected exceptions
        db_session.rollback()
        print(f"Error occurred while deleting account: {e}")
        return jsonify({"detail": "Something went wrong while deleting account.", "status": "error"}), 500
