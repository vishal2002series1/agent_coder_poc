import logging
from pymongo import MongoClient
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FinancialProcessingSystem:
    def __init__(self):
        self.files = {
            "TCATBAL-FILE": None,
            "XREF-FILE": None,
            "DISCGRP-FILE": None,
            "ACCOUNT-FILE": None,
            "TRANSACT-FILE": None
        }
        self.mongo_client = MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo_client["financial_db"]

    def open_file(self, file_name):
        try:
            self.files[file_name] = open(file_name, "r")
            logging.info(f"File {file_name} opened successfully")
            return f"File {file_name} opened"
        except Exception as e:
            logging.error(f"Error opening file {file_name}: {e}")
            raise

    def close_file(self, file_name):
        try:
            if self.files[file_name]:
                self.files[file_name].close()
                logging.info(f"File {file_name} closed successfully")
                return f"File {file_name} closed"
        except Exception as e:
            logging.error(f"Error closing file {file_name}: {e}")
            raise

    def process_records(self, file_name):
        try:
            logging.info(f"Processing records from {file_name}")
            # Simulate record processing
            return f"Processed records from {file_name}"
        except Exception as e:
            logging.error(f"Error processing records from {file_name}: {e}")
            raise

    def fetch_account_data(self, account_id):
        try:
            logging.info(f"Fetching account data for account ID {account_id}")
            account_data = self.db["accounts"].find_one({"account_id": account_id})
            return account_data or {"account_id": account_id, "balance": 1000}
        except Exception as e:
            logging.error(f"Error fetching account data for account ID {account_id}: {e}")
            raise

    def fetch_xref_data(self, account_id):
        try:
            logging.info(f"Fetching cross-reference data for account ID {account_id}")
            xref_data = self.db["xref"].find_one({"xref_id": account_id})
            return xref_data or {"xref_id": account_id, "details": "Sample XREF data"}
        except Exception as e:
            logging.error(f"Error fetching cross-reference data for account ID {account_id}: {e}")
            raise

    def calculate_interest(self, balance, rate):
        try:
            logging.info(f"Calculating interest for balance {balance} with rate {rate}")
            interest = (balance * rate) / 1200
            return interest
        except Exception as e:
            logging.error(f"Error calculating interest: {e}")
            raise

    def update_account(self, account_id, new_balance):
        try:
            logging.info(f"Updating account {account_id} with new balance {new_balance}")
            self.db["accounts"].update_one(
                {"account_id": account_id},
                {"$set": {"balance": new_balance}}
            )
            return f"Account {account_id} updated with balance {new_balance}"
        except Exception as e:
            logging.error(f"Error updating account {account_id}: {e}")
            raise

    def create_transaction_record(self, transaction_details):
        try:
            logging.info(f"Creating transaction record: {transaction_details}")
            self.db["transactions"].insert_one(transaction_details)
            return f"Transaction record created: {transaction_details}"
        except Exception as e:
            logging.error(f"Error creating transaction record: {e}")
            raise

    def fetch_exchange_rates(self, api_url):
        try:
            logging.info(f"Fetching exchange rates from {api_url}")
            response = requests.get(api_url)
            response.raise_for_status()
            exchange_rates = response.json().get("rates", {})
            return exchange_rates
        except Exception as e:
            logging.error(f"Error fetching exchange rates: {e}")
            raise

    def main(self):
        try:
            # Open files
            for file_name in self.files.keys():
                self.open_file(file_name)

            # Process records
            self.process_records("TCATBAL-FILE")

            # Fetch data
            account_data = self.fetch_account_data("12345")
            xref_data = self.fetch_xref_data("12345")

            # Calculate interest
            interest = self.calculate_interest(account_data["balance"], 5)

            # Update account
            new_balance = account_data["balance"] + interest
            self.update_account("12345", new_balance)

            # Create transaction record
            transaction_details = {
                "description": "Interest",
                "amount": interest,
                "timestamp": "2023-01-01"
            }
            self.create_transaction_record(transaction_details)

            # Fetch exchange rates
            self.fetch_exchange_rates("https://api.exchangerate-api.com/v4/latest/USD")

        except Exception as e:
            logging.error(f"An error occurred during processing: {e}")
        finally:
            # Close files
            for file_name in self.files.keys():
                self.close_file(file_name)