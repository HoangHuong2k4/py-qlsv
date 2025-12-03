import pandas as pd

def load_graduate_data(excel_path):
    # use the variable excel_path (not the literal string)
    df = pd.read_excel(excel_path)
    df = df.dropna(subset=['StudentID'])
    if 'Credits' in df.columns:
        df['TotalCredits'] = df.groupby('StudentID')['Credits'].transform('sum')
    else:
        df['TotalCredits'] = 0
    return df
