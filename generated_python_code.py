import os

# File handling functions
def open_file(file_name, mode):
    """
    Opens a file with the given name and mode.
    :param file_name: Name of the file to open.
    :param mode: Mode in which the file should be opened.
    :return: File object.
    """
    return open(file_name, mode)

def read_file(file_obj):
    """
    Reads the content of a file.
    :param file_obj: File object to read from.
    :return: Content of the file.
    """
    return file_obj.read()

def write_file(file_obj, content):
    """
    Writes content to a file.
    :param file_obj: File object to write to.
    :param content: Content to write into the file.
    """
    file_obj.write(content)

def close_file(file_obj):
    """
    Closes the file.
    :param file_obj: File object to close.
    """
    file_obj.close()

# Computation functions
def compute_monthly_interest(tran_cat_bal, dis_int_rate):
    """
    Computes the monthly interest using the formula:
    (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
    :param tran_cat_bal: Transaction category balance.
    :param dis_int_rate: Discount interest rate.
    :return: Monthly interest.
    """
    return (tran_cat_bal * dis_int_rate) / 1200

def compute_total_balance(tran_cat_bal, tran_int_amt):
    """
    Computes the total balance by adding TRAN-CAT-BAL and TRAN-INT-AMT.
    :param tran_cat_bal: Transaction category balance.
    :param tran_int_amt: Transaction interest amount.
    :return: Total balance.
    """
    return tran_cat_bal + tran_int_amt