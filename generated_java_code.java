import java.io.*;
import java.util.*;
import java.util.logging.*;

public class Generated_Java_Code {

    private static final Logger logger = Logger.getLogger(Generated_Java_Code.class.getName());
    private static final Map<String, BufferedReader> openReaders = new HashMap<>();
    private static final Map<String, BufferedWriter> openWriters = new HashMap<>();

    // Open a file for reading or writing
    public static String openFile(String fileName) {
        try {
            if (fileName.equals("TRANSACT-FILE")) {
                BufferedWriter writer = new BufferedWriter(new FileWriter(fileName, true));
                openWriters.put(fileName, writer);
            } else {
                BufferedReader reader = new BufferedReader(new FileReader(fileName));
                openReaders.put(fileName, reader);
            }
            return "File opened";
        } catch (IOException e) {
            logError("Error opening file: " + e.getMessage(), fileName);
            return null;
        }
    }

    // Close a file
    public static boolean closeFile(String fileName) {
        try {
            if (openReaders.containsKey(fileName)) {
                openReaders.get(fileName).close();
                openReaders.remove(fileName);
            } else if (openWriters.containsKey(fileName)) {
                openWriters.get(fileName).close();
                openWriters.remove(fileName);
            }
            return true;
        } catch (IOException e) {
            logError("Error closing file: " + e.getMessage(), fileName);
            return false;
        }
    }

    // Process records from a file
    public static boolean processRecords(String fileName) {
        try {
            BufferedReader reader = openReaders.get(fileName);
            if (reader == null) {
                throw new IllegalStateException("File not opened: " + fileName);
            }

            String line;
            String lastAccountId = null;
            double totalInterest = 0.0;

            while ((line = reader.readLine()) != null) {
                String[] fields = line.split(",");
                String accountId = fields[0];
                double transactionBalance = Double.parseDouble(fields[1]);
                double interestRate = Double.parseDouble(fields[2]);

                if (lastAccountId != null && !lastAccountId.equals(accountId)) {
                    updateAccountBalance("ACCOUNT-FILE", lastAccountId, totalInterest);
                    totalInterest = 0.0;
                }

                double interest = calculateInterest(transactionBalance, interestRate);
                totalInterest += interest;
                lastAccountId = accountId;
            }

            if (lastAccountId != null) {
                updateAccountBalance("ACCOUNT-FILE", lastAccountId, totalInterest);
            }

            return true;
        } catch (Exception e) {
            logError("Error processing records: " + e.getMessage(), fileName);
            return false;
        }
    }

    // Retrieve account data
    public static String retrieveAccountData(String fileName, String accountID) {
        try {
            BufferedReader reader = openReaders.get(fileName);
            if (reader == null) {
                throw new IllegalStateException("File not opened: " + fileName);
            }

            String line;
            while ((line = reader.readLine()) != null) {
                if (line.startsWith(accountID + ",")) {
                    return line;
                }
            }
            return null;
        } catch (IOException e) {
            logError("Error retrieving account data: " + e.getMessage(), fileName);
            return null;
        }
    }

    // Retrieve cross-reference data
    public static String retrieveXrefData(String fileName, String accountID) {
        try {
            BufferedReader reader = openReaders.get(fileName);
            if (reader == null) {
                throw new IllegalStateException("File not opened: " + fileName);
            }

            String line;
            while ((line = reader.readLine()) != null) {
                if (line.startsWith(accountID + ",")) {
                    return line;
                }
            }
            return null;
        } catch (IOException e) {
            logError("Error retrieving cross-reference data: " + e.getMessage(), fileName);
            return null;
        }
    }

    // Calculate monthly interest
    public static double calculateInterest(double balance, double rate) {
        return (balance * rate) / 1200;
    }

    // Update account balance
    public static boolean updateAccountBalance(String fileName, String accountID, double interest) {
        try {
            // Simulate updating account balance in a database or file
            System.out.println("Updated account " + accountID + " with interest: " + interest);
            return true;
        } catch (Exception e) {
            logError("Error updating account balance: " + e.getMessage(), fileName);
            return false;
        }
    }

    // Create a transaction record
    public static boolean createTransactionRecord(String fileName, String description, double amount) {
        try {
            BufferedWriter writer = openWriters.get(fileName);
            if (writer == null) {
                throw new IllegalStateException("File not opened: " + fileName);
            }

            writer.write(description + "," + amount + "," + new Date().toString());
            writer.newLine();
            return true;
        } catch (IOException e) {
            logError("Error creating transaction record: " + e.getMessage(), fileName);
            return false;
        }
    }

    // Handle file errors
    public static boolean handleFileError(String fileName) {
        try {
            // Simulate error handling logic
            System.out.println("Handled error for file: " + fileName);
            return true;
        } catch (Exception e) {
            logError("Error handling file error: " + e.getMessage(), fileName);
            return false;
        }
    }

    // Log errors
    public static boolean logError(String errorMessage, String fileName) {
        try {
            logger.severe("Error in file " + fileName + ": " + errorMessage);
            return true;
        } catch (Exception e) {
            System.err.println("Error logging error: " + e.getMessage());
            return false;
        }
    }
}