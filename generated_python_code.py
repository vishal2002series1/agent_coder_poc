import datetime
import logging

# Configure logging for the audit log
logging.basicConfig(filename='CUSTSTAT.LOG', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

class CustomerAccountStatusUpdater:
    def __init__(self):
        self.current_date = datetime.datetime.now()

    def nightly_batch_process(self):
        """
        Simulates the nightly batch process that updates customer account statuses.
        """
        try:
            # Simulate the COBOL program processing
            self.process_customer_accounts()
            return "Batch process completed"
        except Exception as e:
            self.handle_critical_error(f"Critical error during batch process: {e}")
            return None

    def process_customer_accounts(self):
        """
        Processes customer accounts and updates their statuses based on the rules.
        """
        # Simulated customer data
        customer_data_list = [
            {"CUSTOMER_ID": 1, "CUSTOMER_ACCOUNT_STATUS": "Active", 
             "LAST_PAYMENT_DATE": self.current_date - datetime.timedelta(days=20), 
             "OUTSTANDING_BALANCE_DAYS": 0},
            {"CUSTOMER_ID": 2, "CUSTOMER_ACCOUNT_STATUS": "Active", 
             "LAST_PAYMENT_DATE": self.current_date - datetime.timedelta(days=70), 
             "OUTSTANDING_BALANCE_DAYS": 75},
            {"CUSTOMER_ID": 3, "CUSTOMER_ACCOUNT_STATUS": "Delinquent", 
             "LAST_PAYMENT_DATE": self.current_date - datetime.timedelta(days=100), 
             "OUTSTANDING_BALANCE_DAYS": 95},
            {"CUSTOMER_ID": 4, "CUSTOMER_ACCOUNT_STATUS": "Suspended", 
             "LAST_PAYMENT_DATE": self.current_date - datetime.timedelta(days=200), 
             "OUTSTANDING_BALANCE_DAYS": 0},
        ]

        for customer_data in customer_data_list:
            old_status = customer_data["CUSTOMER_ACCOUNT_STATUS"]
            new_status, reason = self.determine_new_status(customer_data)
            if old_status != new_status:
                customer_data["CUSTOMER_ACCOUNT_STATUS"] = new_status
                self.generate_audit_log(customer_data, old_status, new_status, reason)

    def determine_new_status(self, customer_data):
        """
        Determines the new status for a customer based on their payment history and balance.
        """
        last_payment_date = customer_data.get("LAST_PAYMENT_DATE")
        outstanding_balance_days = customer_data.get("OUTSTANDING_BALANCE_DAYS")
        days_since_last_payment = (self.current_date - last_payment_date).days if last_payment_date else float('inf')

        if days_since_last_payment <= 30 and outstanding_balance_days <= 60:
            return "Active", "Payment received, balance cleared"
        elif 60 < outstanding_balance_days < 90:
            return "Delinquent", "Balance overdue > 60 days"
        elif outstanding_balance_days >= 90 or days_since_last_payment >= 90:
            return "Suspended", "Balance overdue > 90 days or no payment for 90 days"
        elif customer_data["CUSTOMER_ACCOUNT_STATUS"] == "Suspended" and days_since_last_payment >= 180:
            return "Deactivated", "Account suspended for 180 days without payment"
        return customer_data["CUSTOMER_ACCOUNT_STATUS"], "No status change"

    def generate_audit_log(self, customer_data, old_status, new_status, reason):
        """
        Generates an audit log entry for a status change.
        """
        log_message = (f"Customer ID: {customer_data['CUSTOMER_ID']}, "
                       f"Status changed from {old_status} to {new_status}, Reason: {reason}")
        logging.info(log_message)
        return "Audit log generated"

    def handle_critical_error(self, error_message):
        """
        Handles critical errors by logging them and sending an alert.
        """
        logging.error(f"Critical Error: {error_message}")
        # Simulate sending an alert to the Operations team
        print(f"ALERT: {error_message}")
        return "Error handled"