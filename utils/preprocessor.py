import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def load_and_preprocess_alarm_file(file_path: str, output_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, header=1)

    required_columns = [
        "OpenTime", "TTNumber", "Cluster", "SiteID", "SiteName",
        "SourceInput", "EventName", "ClusterEngineer", "Technician",
        "EsclationStatus", "ClearedDateTime"
    ]
    df = df[required_columns].copy()
    df.columns = [col.strip().replace(" ", "_") for col in df.columns]

    # Parse timestamps
    df["OpenTime"] = pd.to_datetime(df["OpenTime"], errors='coerce')
    df["ClearedDateTime"] = pd.to_datetime(df["ClearedDateTime"], errors='coerce')

    # ✅ Remove cleared alarms
    df = df[df["ClearedDateTime"].isna()].copy()

    # Drop ClearedDateTime column since we no longer need it
    df.drop(columns=["ClearedDateTime"], inplace=True)

    # Save cleaned file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Cleaned & filtered file saved at: {output_path}")
    return df
