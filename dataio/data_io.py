import pandas as pd
import openpyxl


def load_xlsx(path):
    return pd.read_excel(path)


def clean_data(df, relevant_columns):
    # Drop missing values in key columns
    df = df.dropna(subset=relevant_columns)

    # Remove unrealistic prices
    df = df[(df['price'] > 100) & (df['price'] < 20000)]

    # Remove rows where price_type is not monthly
    df = df[df['price_type'] == 'Monthly']

    # Remove the price_type column once it's been used to filter
    df = df.drop(columns=['price_type'])

    return df


def load_and_clean_data(path, relevant_columns):
    df = load_xlsx(path)
    return clean_data(df, relevant_columns)


def save_xlsx(df, path):
    df.to_excel(path, index=False)