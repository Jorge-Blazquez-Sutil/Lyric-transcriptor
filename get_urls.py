import pandas as pd
try:
    df = pd.read_excel('uploads/286d07bb-6434-47a0-b0f8-94f5d69a3a18_Muzon.xlsx')
    print("Columns:", list(df.columns))
    for i in range(min(3, len(df))):
        print(f"URL_{i}: {df.iloc[i]['URL']}")
except Exception as e:
    print(f"Error: {e}")
