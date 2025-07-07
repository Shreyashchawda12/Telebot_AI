import pandas as pd

def df_to_dicts(df):
    import numpy as np

    # Convert datetime columns (NaT → None)
    for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
        df[col] = df[col].apply(lambda x: x if pd.notnull(x) else None)

    # Replace NaN in all other columns with None
    df = df.replace({np.nan: None})

    return df.to_dict(orient="records")
