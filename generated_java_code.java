import java.io.*;
import java.util.HashMap;
import java.util.Map;

public class Generated_Java_Code {

    // Map to simulate file storage
    private static final Map<String, String> fileStorage = new HashMap<>();

    /**
     * Opens a file by its name.
     * @param fileName The name of the file to open.
     * @return A message indicating the file has been opened.
     */
    public static String openFile(String fileName) {
        if (fileName == null || fileName.isEmpty()) {
            return "File opened: Invalid file name";
        }
        fileStorage.putIfAbsent(fileName, ""); // Initialize file if not already present
        return "File opened: " + fileName;
    }

    /**
     * Reads the content of a file.
     * @param fileName The name of the file to read.
     * @return The content of the file.
     */
    public static String readFile(String fileName) {
        if (fileName == null || fileName.isEmpty()) {
            return "File content of: Invalid file name";
        }
        return "File content of: " + fileName + " -> " + fileStorage.getOrDefault(fileName, "");
    }

    /**
     * Writes content to a file.
     * @param fileName The name of the file to write to.
     * @param content The content to write to the file.
     * @return A message indicating the content has been written to the file.
     */
    public static String writeFile(String fileName, String content) {
        if (fileName == null || fileName.isEmpty()) {
            return "Written to file: Invalid file name";
        }
        fileStorage.put(fileName, content);
        return "Written to file: " + fileName;
    }

    /**
     * Closes a file by its name.
     * @param fileName The name of the file to close.
     * @return A message indicating the file has been closed.
     */
    public static String closeFile(String fileName) {
        if (fileName == null || fileName.isEmpty()) {
            return "File closed: Invalid file name";
        }
        return "File closed: " + fileName;
    }

    /**
     * Computes the monthly interest using the formula:
     * (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
     * @param tranCatBal The transaction category balance.
     * @param disIntRate The discount interest rate.
     * @return The computed monthly interest.
     */
    public static Double computeMonthlyInterest(double tranCatBal, double disIntRate) {
        return (tranCatBal * disIntRate) / 1200;
    }

    /**
     * Computes the total balance by adding TRAN-CAT-BAL and TRAN-INT-AMT.
     * @param tranCatBal The transaction category balance.
     * @param tranIntAmt The transaction interest amount.
     * @return The computed total balance.
     */
    public static Double computeTotalBalance(double tranCatBal, double tranIntAmt) {
        return tranCatBal + tranIntAmt;
    }

    public static void main(String[] args) {
        // This main method is provided for manual execution if needed.
        // The actual tests are defined in the RelaxedTests class.
        System.out.println("Generated_Java_Code is ready to run with the provided tests.");
    }
}