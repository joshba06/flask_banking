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


category
- (String): Transaction category.
- Must be one of the following: ["Transfer", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"]:

!- a standard transaction cannot have "Transfer" as a category.
!- a subaccount can only have "Transfer" as a category.


time_booked
- (DateTime)
- Store time in db as UTC
- Display time in local time
- Convert time provided by API request to UTC



account_id (Integer): Foreign Key from "accounts" table.
