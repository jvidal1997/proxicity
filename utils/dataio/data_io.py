"""
IO utility functions for loading, cleaning, and saving Excel-based tabular data.

This module provides a small data-processing pipeline built around Pandas:
    - `load_xlsx` reads an Excel file into a DataFrame and validates its existence.
    - `clean_data` applies a series of cleaning operations, including removal of
      missing values, unrealistic price ranges, and non-monthly price entries.
    - `load_and_clean_data` combines the above steps and logs any errors through
      the asynchronous logger.
    - `save_xlsx` exports a cleaned DataFrame back to an Excel file.

The cleaning logic assumes the presence of certain columns, such as `price` and
`price_type`, and uses a `relevant_columns` list (typically supplied by a
Settings object) to determine which fields must not contain missing values.

Logging is handled through `AsyncFileLogger`, which captures and records errors
encountered during reading or cleaning.

Dependencies:
    - pandas
    - openpyxl
    - devtools.multithread_logger.AsyncFileLogger

Intended use:
    Import these utilities into data-processing workflows that operate on Excel
    datasets, particularly where filtering by price and price_type is
    required.
"""
import os.path
import pandas as pd
from utils.devtools.multithread_logger import AsyncFileLogger
from Settings import ENV as PROPERTY

# Instantiate logger
log = AsyncFileLogger()


def load_xlsx(path):
    """
    Reads an Excel file into a Pandas Dataframe Object
    :param path: Path to the Excel file.
    :return: pd.DataFrame: Pandas Dataframe Object
    :raises FileNotFoundError: If file does not exist.
    """
    if os.path.exists(path):
        return pd.read_excel(path)
    else:
        raise FileNotFoundError(f"Excel file not found: {path}")


def clean_data(df, relevant_columns):
    """
    Cleans the provided DataFrame by removing the following:
        - rows with missing values
        - unrealistic prices
        - rows where price_type is not monthly
        - price_type column after all other removals.
    :param df: Pandas DataFrame Object
    :param relevant_columns: imported from the Settings object
    :return: Pandas DataFrame Object
    """
    # Drop missing values in key columns
    df = df.dropna(subset=relevant_columns)

    # Remove unrealistic prices
    df = df[(df['price'] > PROPERTY['MIN_PRICE']) & (df['price'] < PROPERTY['MAX_PRICE'])]

    # Remove rows where price_type is not monthly
    df = df[df['price_type'] == 'Monthly']

    # Remove the price_type column once it's been used to filter
    df = df.drop(columns=['price_type'])

    return df


def load_and_clean_data(path, relevant_columns):
    """
    Reads an Excel file into a Pandas Dataframe Object and cleans the provided DataFrame by removing the following:
        - rows with missing values
        - unrealistic prices
        - rows where price_type is not monthly
        - price_type column after all other removals.
    :param path: Path to the Excel file.
    :param relevant_columns: imported from the Settings object
    :return: Pandas DataFrame Object
    :raises FileNotFoundError: If file does not exist.
    """
    try:
        df = load_xlsx(path)
        return clean_data(df, relevant_columns)
    except Exception as e:
        log.error(f"{e}")
        raise e


def save_xlsx(df, path):
    """
    Saves a Pandas DataFrame object to an Excel file.
    :param df: Pandas DataFrame Object
    :param path: Path to the Excel file.
    :return: None
    """
    df.to_excel(path, index=False)
    print(f"Excel file saved to {path}")