import logging
import boto3
import sqlite3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class FinancialProcessingSystem:
    def __init__(self):
        # AWS S3 client setup
        self.s3_client = boto3.client('s3')
        self.bucket_name = "financial-data-bucket"

        # SQLite database connection
        self.db_connection = sqlite3.connect("financial_data.db")
        self.cursor = self.db_connection.cursor()

        # File handles
        self.file_handles = {}

    def open_file(self, file_name):
        try:
            # Simulate downloading file from S3
            local_file_path = f"./{file_name}"
            self.s3_client.download_file(self.bucket_name, file_name, local_file_path)
            self.file_handles[file_name] = open(local_file_path, 'r')
            return f"File {file_name} opened"
        except (NoCredentialsError, PartialCredentialsError) as e:
            self.log_error(f"Error downloading file {file_name} from S3: {e}")
            raise
        except Exception as e:
            self.log_error(f"Error opening file {file_name}: {e}")
            raise

    def close_file(self, file_name):
        try:
            if file_name in self.file_handles:
                self.file_handles[file_name].close()
                del self.file_handles[file_name]
                return f"File {file_name} closed"
        except Exception as e:
            self.log_error(f"Error closing file {file_name}: {e}")
            raise

    def process_records(self, file_name):
        try:
            if file_name not in self.file_handles:
                raise Exception(f"File {file_name} is not open")
            record_count = 0
            total_interest = 0
            last_account_id = None

            for line in self.file_handles[file_name]:
                record = line.strip().split(",")  # Assuming CSV format
                account_id, balance, category = record
                balance = float(balance)

                if last_account_id and last_account_id != account_id:
                    self.update_account(last_account_id, total_interest)
                    total_interest = 0

                interest_rate = self.fetch_interest_rate(category)
                interest = self.calculate_interest(balance, interest_rate)
                total_interest += interest
                last_account_id = account_id
                record_count += 1

            if last_account_id:
                self.update_account(last_account_id, total_interest)

            return f"Processed {record_count} records from {file_name}"
        except Exception as e:
            self.log_error(f"Error processing records from {file_name}: {e}")
            raise

    def fetch_data(self, file_name, account_id):
        try:
            if file_name == "ACCOUNT-FILE":
                query = "SELECT * FROM accounts WHERE account_id = ?"
            elif file_name == "XREF-FILE":
                query = "SELECT * FROM cross_reference WHERE account_id = ?"
            else:
                raise Exception(f"Unsupported file for data fetching: {file_name}")

            self.cursor.execute(query, (account_id,))
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            self.log_error(f"Error fetching data from {file_name} for account {account_id}: {e}")
            raise

    def fetch_interest_rate(self, category):
        try:
            query = "SELECT interest_rate FROM discount_groups WHERE category = ?"
            self.cursor.execute(query, (category,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                # Fetch default interest rate
                query = "SELECT interest_rate FROM discount_groups WHERE category = 'DEFAULT'"
                self.cursor.execute(query)
                result = self.cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            self.log_error(f"Error fetching interest rate for category {category}: {e}")
            raise

    def calculate_interest(self, balance, rate):
        try:
            return (balance * rate) / 1200
        except Exception as e:
            self.log_error(f"Error calculating interest: {e}")
            raise

    def update_account(self, account_id, interest):
        try:
            query = "UPDATE accounts SET balance = balance + ?, cycle_credit = 0, cycle_debit = 0 WHERE account_id = ?"
            self.cursor.execute(query, (interest, account_id))
            self.db_connection.commit()
            return f"Updated account {account_id} with interest {interest}"
        except Exception as e:
            self.log_error(f"Error updating account {account_id}: {e}")
            raise

    def create_transaction_record(self, interest):
        try:
            query = "INSERT INTO transactions (description, amount, timestamp) VALUES (?, ?, datetime('now'))"
            self.cursor.execute(query, ("Interest Calculation", interest))
            self.db_connection.commit()
            return f"Transaction record created for interest {interest}"
        except Exception as e:
            self.log_error(f"Error creating transaction record for interest {interest}: {e}")
            raise

    def log_error(self, message):
        logging.error(message)
        return f"Logged error: {message}"

    def __del__(self):
        # Ensure all files are closed and database connection is closed
        for file_name in list(self.file_handles.keys()):
            self.close_file(file_name)
        self.db_connection.close()