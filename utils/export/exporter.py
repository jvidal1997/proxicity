"""
Provides utility functions to export summary statistics and correlation matrices of apartment/listing data
to Excel files.

Functions:
- export_summary(df, path): Exports descriptive statistics of the DataFrame to an Excel file.
- export_correlation(df, path): Exports the correlation matrix of the DataFrame to an Excel file.
"""


def export_summary(df, path):
    """
    Exports descriptive statistics of the DataFrame (count, mean, std, min, max, quartiles)
    to an Excel file at the specified path.
    :param df: DataFrame of apartment prices and distances to city centers and landmarks.
    :param path: Path to output Excel file.
    """
    df.describe().to_excel(path, index=False)


def export_correlation(df, path):
    """
    Exports the correlation matrix of the DataFrame to an Excel file at the specified path.
    :param df: DataFrame of apartment prices and distances to city centers and landmarks.
    :param path: Path to output Excel file.
    """
    df.corr().to_excel(path, index=False)