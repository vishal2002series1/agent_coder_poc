import java.io.*;
import java.util.*;
import java.util.logging.*;

public class Generated_Java_Code {

    // Logger for error handling and logging
    private static final Logger logger = Logger.getLogger(Generated_Java_Code.class.getName());

    // File names
    private static final String TCATBAL_FILE = "TCATBAL-FILE";
    private static final String XREF_FILE = "XREF-FILE";
    private static final String DISCGRP_FILE = "DISCGRP-FILE";
    private static final String ACCOUNT_FILE = "ACCOUNT-FILE";
    private static final String TRANSACT_FILE = "TRANSACT-FILE";

    // File handles
    private BufferedReader tcatbalReader;
    private BufferedReader xrefReader;
    private BufferedReader discgrpReader;
    private BufferedReader accountReader;
    private BufferedWriter transactWriter;

    // Data structures for processing
    private Map<String, String> accountData = new HashMap<>();
    private Map<String, String> xrefData = new HashMap<>();
    private Map<String, Double> interestRates = new HashMap<>();

    // Open all required files
    public void openFiles() {
        try {
            tcatbalReader = new BufferedReader(new FileReader(TCATBAL_FILE));
            xrefReader = new BufferedReader(new FileReader(XREF_FILE));
            discgrpReader = new BufferedReader(new FileReader(DISCGRP_FILE));
            accountReader = new BufferedReader(new FileReader(ACCOUNT_FILE));
            transactWriter = new BufferedWriter(new FileWriter(TRANSACT_FILE, true));
        } catch (IOException e) {
            logger.severe("Error opening files: " + e.getMessage());
            throw new RuntimeException("Failed to open files", e);
        }
    }

    // Close all opened files
    public void closeFiles() {
        try {
            if (tcatbalReader != null) tcatbalReader.close();
            if (xrefReader != null) xrefReader.close();
            if (discgrpReader != null) discgrpReader.close();
            if (accountReader != null) accountReader.close();
            if (transactWriter != null) transactWriter.close();
        } catch (IOException e) {
            logger.severe("Error closing files: " + e.getMessage());
        }
    }

    // Process records from TCATBAL-FILE
    public void processRecords() {
        try {
            String line;
            int recordCount = 0;
            String previousAccountId = null;
            double accumulatedInterest = 0.0;

            while ((line = tcatbalReader.readLine()) != null) {
                recordCount++;
                String[] fields = line.split(",");
                String accountId = fields[0];
                double transactionBalance = Double.parseDouble(fields[1]);
                String transactionCategory = fields[2];

                if (!accountId.equals(previousAccountId) && previousAccountId != null) {
                    updateAccount(previousAccountId, accumulatedInterest);
                    accumulatedInterest = 0.0;
                }

                double interestRate = getInterestRate(accountId, transactionCategory);
                double monthlyInterest = (transactionBalance * interestRate) / 1200;
                accumulatedInterest += monthlyInterest;

                previousAccountId = accountId;
            }

            if (previousAccountId != null) {
                updateAccount(previousAccountId, accumulatedInterest);
            }

        } catch (IOException e) {
            logger.severe("Error processing records: " + e.getMessage());
        }
    }

    // Retrieve account and cross-reference data
    public void retrieveData() {
        try {
            String line;

            while ((line = accountReader.readLine()) != null) {
                String[] fields = line.split(",");
                accountData.put(fields[0], line); // Account ID as key
            }

            while ((line = xrefReader.readLine()) != null) {
                String[] fields = line.split(",");
                xrefData.put(fields[0], line); // Cross-reference ID as key
            }

        } catch (IOException e) {
            logger.severe("Error retrieving data: " + e.getMessage());
        }
    }

    // Calculate interest rate from DISCGRP-FILE
    private double getInterestRate(String accountId, String transactionCategory) {
        try {
            String accountGroupId = xrefData.get(accountId).split(",")[1];
            String key = accountGroupId + "-" + transactionCategory;

            if (interestRates.containsKey(key)) {
                return interestRates.get(key);
            }

            String line;
            while ((line = discgrpReader.readLine()) != null) {
                String[] fields = line.split(",");
                String groupKey = fields[0] + "-" + fields[1];
                double rate = Double.parseDouble(fields[2]);
                interestRates.put(groupKey, rate);

                if (groupKey.equals(key)) {
                    return rate;
                }
            }

        } catch (IOException e) {
            logger.severe("Error retrieving interest rate: " + e.getMessage());
        }

        return 0.0; // Default interest rate
    }

    // Update account balances
    private void updateAccount(String accountId, double accumulatedInterest) {
        try {
            String accountRecord = accountData.get(accountId);
            String[] fields = accountRecord.split(",");
            double currentBalance = Double.parseDouble(fields[2]);
            double updatedBalance = currentBalance + accumulatedInterest;

            // Update account record
            fields[2] = String.valueOf(updatedBalance);
            accountData.put(accountId, String.join(",", fields));

            // Write transaction record
            createTransactionRecord(accountId, accumulatedInterest);

        } catch (Exception e) {
            logger.severe("Error updating account: " + e.getMessage());
        }
    }

    // Create transaction record
    private void createTransactionRecord(String accountId, double amount) {
        try {
            String transactionRecord = accountId + "," + amount + "," + new Date().toString();
            transactWriter.write(transactionRecord);
            transactWriter.newLine();
        } catch (IOException e) {
            logger.severe("Error creating transaction record: " + e.getMessage());
        }
    }

    // Main method to execute the program
    public static void main(String[] args) {
        Generated_Java_Code program = new Generated_Java_Code();

        try {
            program.openFiles();
            program.retrieveData();
            program.processRecords();
        } finally {
            program.closeFiles();
        }
    }
}