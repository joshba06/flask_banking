Software Design Document (SDD) for Banking System
1. Introduction:
This document describes the design of a banking system with functionality to manage accounts and their associated transactions.

2. System Architecture:
Components:
1. Account:
Manages the account details of users.
Ensures uniqueness of IBAN.
Validates title and IBAN during initialization.
2. Transaction:
Handles all transactional data associated with an account.
Manages the computation of the account balance.
Enables filtering and grouping of transactions.

3. Data Design:
Tables:
1 accounts:

id (Integer): Primary Key.
title (String):
- string between 3 and 15 characters long
- Cannot start with digit

iban (String): Unique bank account number.
- Generated in backend, not by user


2 transactions:

id
- (Integer) Primary Key.

description
- (String): Transaction description.
- string between 1 and 80 characters long (cannot be empty string " ", "")
- may start with digit
- Cannot be None


amount
- (Numeric) Transaction amount with precision.
- may ne positive or negative, cannot be 0
- Cannot be string or any other datatype, must be float

saldo
- (Numeric)
- May be negative or positive (doesnt throw error if transaction is initiated but balance is negative)

category
- (String): Transaction category.
- Must be one of the following: ["Transfer", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"]:

!- a standard transaction cannot have "Transfer" as a category.
!- a subaccount can only have "Transfer" as a category.


utc_datetime_booked
- DateTime
- Store time in db as UTC (without timezone information, since all datetime objects are stored in UTC)
- API:
  - Return time with UTC format information
  - Post request for new transaction must have datetime as isoformat string in UTC format (converted to datetime object in API endpoint)
- Webroute:
  - Form does not allow time selection, thus default server time is used for new transaction
  - Transactions are displayed with date, not time. Time is only used for sorting (which is all in UTC so no conversion needed)



account_id (Integer): Foreign Key from "accounts" table.
