import logging
from pymongo import MongoClient
import requests

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class FinancialProcessingSystem:
    def __init__(self):
        self.files = {}
        self.mongo_client = MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo_client["financial_db"]

    def open_file(self, file_name):
        try:
            file_obj = open(file_name, 'w')
            self.files[file_name] = file_obj
            return file_obj
        except Exception as e:
            logging.error(f"Error opening file {file_name}: {e}")
            raise

    def close_file(self, file_obj):
        try:
            file_obj.close()
        except Exception as e:
            logging.error(f"Error closing file: {e}")
            raise

    def process_records(self, file_name):
        try:
            with open(file_name, 'r') as file:
                record_count = 0
                previous_account_id = None
                total_interest = 0

                for line in file:
                    record_count += 1
                    record = line.strip().split(",")  # Assuming CSV format
                    account_id = record[0]
                    balance = float(record[1])
                    group_id = record[2]

                    if account_id != previous_account_id and previous_account_id is not None:
                        self.update_account_balance(previous_account_id, total_interest)
                        total_interest = 0

                    interest_rate = self.fetch_interest_rate(group_id)
                    interest = self.calculate_interest(balance, interest_rate)
                    total_interest += interest
                    previous_account_id = account_id

                if previous_account_id is not None:
                    self.update_account_balance(previous_account_id, total_interest)

            return True
        except Exception as e:
            logging.error(f"Error processing records from {file_name}: {e}")
            raise

    def fetch_account_data(self, account_id):
        try:
            account_data = self.db["accounts"].find_one({"account_id": account_id})
            return account_data
        except Exception as e:
            logging.error(f"Error fetching account data for account ID {account_id}: {e}")
            raise

    def fetch_cross_reference_data(self, account_id):
        try:
            xref_data = self.db["cross_references"].find_one({"xref_id": account_id})
            return xref_data
        except Exception as e:
            logging.error(f"Error fetching cross-reference data for account ID {account_id}: {e}")
            raise

    def fetch_interest_rate(self, group_id):
        try:
            rate_data = self.db["discount_groups"].find_one({"group_id": group_id})
            if rate_data:
                return rate_data.get("interest_rate", 0)
            else:
                default_rate_data = self.db["discount_groups"].find_one({"group_id": "default"})
                return default_rate_data.get("interest_rate", 0) if default_rate_data else 0
        except Exception as e:
            logging.error(f"Error fetching interest rate for group ID {group_id}: {e}")
            raise

    def calculate_interest(self, balance, rate):
        try:
            return (balance * rate) / 1200
        except Exception as e:
            logging.error(f"Error calculating interest: {e}")
            raise

    def update_account_balance(self, account_id, accumulated_interest):
        try:
            account_data = self.fetch_account_data(account_id)
            if account_data:
                new_balance = account_data["balance"] + accumulated_interest
                self.db["accounts"].update_one(
                    {"account_id": account_id},
                    {"$set": {"balance": new_balance, "cycle_credit": 0, "cycle_debit": 0}}
                )
                return True
            return False
        except Exception as e:
            logging.error(f"Error updating account balance for account ID {account_id}: {e}")
            raise

    def create_transaction_record(self, transaction_details):
        try:
            self.db["transactions"].insert_one(transaction_details)
            return True
        except Exception as e:
            logging.error(f"Error creating transaction record: {e}")
            raise

    def fetch_stock_prices(self, ticker_symbols):
        try:
            stock_prices = {}
            for symbol in ticker_symbols:
                response = requests.get(f"https://api.example.com/stock/{symbol}")
                if response.status_code == 200:
                    data = response.json()
                    stock_prices[symbol] = data.get("current_price", 0)
                else:
                    logging.error(f"Error fetching stock price for {symbol}: {response.status_code}")
            return stock_prices
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while fetching stock prices: {e}")
            raise

    def close_all_files(self):
        try:
            for file_obj in self.files.values():
                self.close_file(file_obj)
        except Exception as e:
            logging.error(f"Error closing all files: {e}")
            raise