import java.io.*;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class Generated_Java_Code {

    // Data structure to represent a customer account
    static class CustomerAccount {
        String accountId;
        String status;
        LocalDate lastPaymentDate;
        LocalDate lastActivityDate;
        LocalDate oldestOutstandingBalanceDate;

        public CustomerAccount(String accountId, String status, LocalDate lastPaymentDate, LocalDate lastActivityDate, LocalDate oldestOutstandingBalanceDate) {
            this.accountId = accountId;
            this.status = status;
            this.lastPaymentDate = lastPaymentDate;
            this.lastActivityDate = lastActivityDate;
            this.oldestOutstandingBalanceDate = oldestOutstandingBalanceDate;
        }
    }

    // Method to simulate the nightly batch process
    public static String runNightlyBatchProcess(String inputFile) {
        try {
            if (inputFile == null || inputFile.isEmpty()) {
                throw new IllegalArgumentException("Input file is empty or null");
            }

            // Simulate reading customer data from a file
            List<CustomerAccount> customerAccounts = readCustomerData(inputFile);

            // Update customer account statuses
            List<String> auditLogs = new ArrayList<>();
            for (CustomerAccount account : customerAccounts) {
                String oldStatus = account.status;
                String newStatus = determineNewStatus(account);
                if (!oldStatus.equals(newStatus)) {
                    account.status = newStatus;
                    auditLogs.add(generateAuditLogEntry(account.accountId, oldStatus, newStatus, getReasonForChange(oldStatus, newStatus)));
                }
            }

            // Write audit logs to a file
            writeAuditLog(auditLogs);

            return "Batch Process Completed";
        } catch (Exception e) {
            handleCriticalError(e.getMessage());
            return "Batch Process Failed";
        }
    }

    // Method to determine the new status of a customer account
    public static String determineNewStatus(CustomerAccount account) {
        LocalDate today = LocalDate.now();

        if (account.lastPaymentDate != null && account.lastPaymentDate.isAfter(today.minusDays(30)) &&
            (account.oldestOutstandingBalanceDate == null || account.oldestOutstandingBalanceDate.isAfter(today.minusDays(60)))) {
            return "Active";
        } else if (account.oldestOutstandingBalanceDate != null && account.oldestOutstandingBalanceDate.isAfter(today.minusDays(90)) &&
                   account.oldestOutstandingBalanceDate.isBefore(today.minusDays(60))) {
            return "Delinquent";
        } else if ((account.oldestOutstandingBalanceDate != null && account.oldestOutstandingBalanceDate.isBefore(today.minusDays(90))) ||
                   (account.lastPaymentDate == null || account.lastPaymentDate.isBefore(today.minusDays(90)))) {
            return "Suspended";
        } else if (account.status.equals("Suspended") && account.lastPaymentDate == null &&
                   account.lastActivityDate != null && account.lastActivityDate.isBefore(today.minusDays(180))) {
            return "Deactivated";
        }

        return account.status;
    }

    // Method to generate an audit log entry
    public static String generateAuditLogEntry(String accountId, String oldStatus, String newStatus, String reason) {
        return String.format("Account ID: %s, Old Status: %s, New Status: %s, Reason: %s", accountId, oldStatus, newStatus, reason);
    }

    // Method to get the reason for a status change
    public static String getReasonForChange(String oldStatus, String newStatus) {
        if (newStatus.equals("Active")) {
            return "Payment received, balance cleared";
        } else if (newStatus.equals("Delinquent")) {
            return "Balance overdue > 60 days";
        } else if (newStatus.equals("Suspended")) {
            return "Balance overdue > 90 days or no payment activity for 90 days";
        } else if (newStatus.equals("Deactivated")) {
            return "Account suspended for 180 days without activity";
        }
        return "No change";
    }

    // Method to write audit logs to a file
    public static void writeAuditLog(List<String> auditLogs) throws IOException {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("CUSTSTAT.LOG"))) {
            for (String log : auditLogs) {
                writer.write(log);
                writer.newLine();
            }
        }
    }

    // Method to handle critical errors
    public static String handleCriticalError(String errorDetails) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("CUSTSTAT.LOG", true))) {
            writer.write("Critical Error: " + errorDetails);
            writer.newLine();
        } catch (IOException e) {
            System.err.println("Failed to log critical error: " + e.getMessage());
        }
        // Simulate sending an alert to the Operations team
        System.err.println("ALERT: " + errorDetails);
        return "Error Handled";
    }

    // Method to simulate reading customer data from a file
    public static List<CustomerAccount> readCustomerData(String inputFile) throws IOException {
        List<CustomerAccount> accounts = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(inputFile))) {
            String line;
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                String accountId = parts[0];
                String status = parts[1];
                LocalDate lastPaymentDate = parts[2].isEmpty() ? null : LocalDate.parse(parts[2], formatter);
                LocalDate lastActivityDate = parts[3].isEmpty() ? null : LocalDate.parse(parts[3], formatter);
                LocalDate oldestOutstandingBalanceDate = parts[4].isEmpty() ? null : LocalDate.parse(parts[4], formatter);
                accounts.add(new CustomerAccount(accountId, status, lastPaymentDate, lastActivityDate, oldestOutstandingBalanceDate));
            }
        }
        return accounts;
    }

    // Main method to simulate the nightly batch process
    public static void main(String[] args) {
        String result = runNightlyBatchProcess("customer_transactions.txt");
        System.out.println(result);
    }
}