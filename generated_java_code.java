import java.util.*;
import java.io.*;
import java.util.logging.*;

public class Solution {

    private static final Logger logger = Logger.getLogger(Solution.class.getName());

    public static void main(String[] args) {
        try {
            // Step 1: Open Required Files
            List<String> files = Arrays.asList("TCATBAL-FILE", "XREF-FILE", "DISCGRP-FILE", "ACCOUNT-FILE", "TRANSACT-FILE");
            Map<String, BufferedReader> fileReaders = openFiles(files);

            // Step 2: Process Records from TCATBAL-FILE
            processRecords(fileReaders.get("TCATBAL-FILE"));

            // Step 3: Close All Files
            closeFiles(fileReaders);

        } catch (Exception e) {
            logger.severe("An error occurred: " + e.getMessage());
        }
    }

    // Method to open required files
    public static Map<String, BufferedReader> openFiles(List<String> files) throws IOException {
        Map<String, BufferedReader> fileReaders = new HashMap<>();
        for (String file : files) {
            try {
                System.out.println("Opening file: " + file);
                fileReaders.put(file, new BufferedReader(new FileReader(file)));
            } catch (IOException e) {
                logger.severe("Error opening file: " + file + " - " + e.getMessage());
                throw e;
            }
        }
        return fileReaders;
    }

    // Method to close all opened files
    public static void closeFiles(Map<String, BufferedReader> fileReaders) {
        for (Map.Entry<String, BufferedReader> entry : fileReaders.entrySet()) {
            try {
                System.out.println("Closing file: " + entry.getKey());
                entry.getValue().close();
            } catch (IOException e) {
                logger.warning("Error closing file: " + entry.getKey() + " - " + e.getMessage());
            }
        }
    }

    // Method to process records from TCATBAL-FILE
    public static void processRecords(BufferedReader tcatbalFileReader) throws IOException {
        String line;
        int recordCount = 0;
        String lastAccountId = null;
        double accumulatedInterest = 0.0;

        while ((line = tcatbalFileReader.readLine()) != null) {
            recordCount++;
            System.out.println("Processing record: " + line);

            // Simulate extracting account ID and transaction balance
            String[] recordParts = line.split(",");
            String accountId = recordParts[0];
            double transactionBalance = Double.parseDouble(recordParts[1]);

            // Check if account ID has changed
            if (lastAccountId != null && !lastAccountId.equals(accountId)) {
                // Update account with accumulated interest
                updateAccount(lastAccountId, accumulatedInterest);
                accumulatedInterest = 0.0; // Reset accumulated interest
            }

            // Calculate interest for the current record
            double interestRate = getInterestRate(accountId);
            double monthlyInterest = calculateMonthlyInterest(transactionBalance, interestRate);
            accumulatedInterest += monthlyInterest;

            lastAccountId = accountId;
        }

        // Update the last account with accumulated interest
        if (lastAccountId != null) {
            updateAccount(lastAccountId, accumulatedInterest);
        }

        System.out.println("Total records processed: " + recordCount);
    }

    // Method to calculate monthly interest
    public static double calculateMonthlyInterest(double transactionBalance, double interestRate) {
        return (transactionBalance * interestRate) / 1200;
    }

    // Simulated method to retrieve interest rate
    public static double getInterestRate(String accountId) {
        // Simulate fetching interest rate from DISCGRP-FILE
        return 5.0; // Default interest rate
    }

    // Simulated method to update account with accumulated interest
    public static void updateAccount(String accountId, double accumulatedInterest) {
        System.out.println("Updating account: " + accountId + " with accumulated interest: " + accumulatedInterest);
        // Simulate updating account in MongoDB
    }
}