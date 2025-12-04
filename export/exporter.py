def export_summary(df, path):
    df.describe().to_excel(path, index=False)


def export_correlation(df, path):
    df.corr().to_excel(path, index=False)