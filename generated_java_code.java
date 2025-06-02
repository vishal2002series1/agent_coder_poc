import java.io.*;
import java.util.*;
import java.util.logging.*;
import java.net.*;
import com.fasterxml.jackson.databind.ObjectMapper; // For JSON parsing using Jackson
import com.fasterxml.jackson.core.type.TypeReference;

public class Solution {

    private static final Logger logger = Logger.getLogger(Solution.class.getName());

    // Method to open required files for processing
    public static void openFiles(Map<String, BufferedReader> files) throws IOException {
        for (Map.Entry<String, BufferedReader> entry : files.entrySet()) {
            if (entry.getValue() == null) {
                throw new IOException("File " + entry.getKey() + " could not be opened.");
            }
        }
        logger.info("All files opened successfully.");
    }

    // Method to close all files after processing
    public static void closeFiles(Map<String, BufferedReader> files) throws IOException {
        for (Map.Entry<String, BufferedReader> entry : files.entrySet()) {
            try {
                if (entry.getValue() != null) {
                    entry.getValue().close();
                }
            } catch (IOException e) {
                logger.warning("Error closing file " + entry.getKey() + ": " + e.getMessage());
            }
        }
        logger.info("All files closed successfully.");
    }

    // Method to process records from Transaction Category Balance File
    public static void processRecords(BufferedReader file) throws IOException {
        String line;
        int recordCount = 0;
        String previousAccountId = null;
        double totalInterest = 0.0;

        while ((line = file.readLine()) != null) {
            recordCount++;
            String[] recordParts = line.split(","); // Assuming CSV format
            String accountId = recordParts[0];
            double transactionBalance = Double.parseDouble(recordParts[1]);
            double interestRate = Double.parseDouble(recordParts[2]);

            if (!accountId.equals(previousAccountId) && previousAccountId != null) {
                // Update account with accumulated interest
                updateAccountBalances(Map.of(previousAccountId, totalInterest));
                totalInterest = 0.0;
            }

            totalInterest += calculateMonthlyInterest(transactionBalance, interestRate);
            previousAccountId = accountId;
        }

        // Final update for the last account
        if (previousAccountId != null) {
            updateAccountBalances(Map.of(previousAccountId, totalInterest));
        }

        logger.info("Processed " + recordCount + " records.");
    }

    // Method to retrieve account and cross-reference data
    public static void retrieveAccountAndXrefData(Map<String, String> accountData, Map<String, String> xrefData) {
        // Simulate retrieval logic
        logger.info("Retrieved account and cross-reference data.");
    }

    // Method to calculate monthly interest
    public static double calculateMonthlyInterest(double transactionBalance, double interestRate) {
        return (transactionBalance * interestRate) / 1200.0;
    }

    // Method to update account balances
    public static void updateAccountBalances(Map<String, Double> accountData) {
        for (Map.Entry<String, Double> entry : accountData.entrySet()) {
            String accountId = entry.getKey();
            double accumulatedInterest = entry.getValue();
            logger.info("Updated account " + accountId + " with interest: " + accumulatedInterest);
        }
    }

    // Method to create transaction records for calculated interest
    public static void createTransactionRecords(List<String> transactions) {
        for (String transaction : transactions) {
            logger.info("Created transaction record: " + transaction);
        }
    }

    // Method to fetch and process currency exchange rates from external API
    public static Map<String, Double> fetchAndProcessExchangeRates(String apiResponse) throws IOException {
        ObjectMapper objectMapper = new ObjectMapper();
        Map<String, Object> responseMap = objectMapper.readValue(apiResponse, new TypeReference<Map<String, Object>>() {});
        Map<String, Double> rates = (Map<String, Double>) responseMap.get("rates");
        logger.info("Fetched and processed exchange rates: " + rates);
        return rates;
    }

    // Method to fetch exchange rates from an external API
    public static Map<String, Double> fetchExchangeRatesFromApi(String apiUrl) throws IOException {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(apiUrl);
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(5000);

            int responseCode = connection.getResponseCode();
            if (responseCode != 200) {
                throw new IOException("Failed to fetch exchange rates. HTTP response code: " + responseCode);
            }

            BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();

            return fetchAndProcessExchangeRates(response.toString());
        } catch (IOException e) {
            logger.severe("Error fetching exchange rates: " + e.getMessage());
            throw e;
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }
}