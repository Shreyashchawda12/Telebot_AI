import pandas as pd
import requests
from datetime import datetime, timedelta

# --- Configuration ---
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CLEANED_ALARM_FILE = "data/processed/cleaned_alarms.csv"
MAPPING_FILE = "data/mapping/site_escalation_mapping.xlsx"

# --- Helper to send message via Telegram ---
def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    return response.status_code == 200

# --- Load and process data ---
def load_and_merge():
    alarm_df = pd.read_csv(CLEANED_ALARM_FILE)
    mapping_df = pd.read_excel(MAPPING_FILE)

    merged_df = pd.merge(alarm_df, mapping_df, how='left', on='GLOBAL SITE ID')
    merged_df['OpenTime'] = pd.to_datetime(merged_df['OpenTime'])
    return merged_df

# --- Escalation Logic ---
def escalate_alarms():
    df = load_and_merge()
    now = datetime.now()

    # Escalate to Technicians and Supervisors
    for _, row in df.iterrows():
        msg = f"\ud83d\udea8 <b>Alarm Escalation</b>\n\n<b>Site:</b> {row['SITE NAME']}\n<b>Cluster:</b> {row['CLUSTER']}\n<b>Alarm:</b> {row['Standard_Alarm_Name']}\n<b>Time:</b> {row['OpenTime']}\n<b>TT No:</b> {row['TTNumber']}"

        # Technician
        if not pd.isna(row['Technician Chat ID']):
            send_telegram_message(int(row['Technician Chat ID']), msg)

        # Supervisor
        if not pd.isna(row['Supervisor Chat ID']):
            send_telegram_message(int(row['Supervisor Chat ID']), msg)

    # Escalate to CE only for long pending > 1 hour
    df['PendingDuration'] = now - df['OpenTime']
    long_pending_df = df[df['PendingDuration'] > timedelta(hours=1)]

    for _, row in long_pending_df.iterrows():
        msg = f"\u26a0\ufe0f <b>Long Pending Alarm (>1hr)</b>\n\n<b>Site:</b> {row['SITE NAME']}\n<b>Cluster:</b> {row['CLUSTER']}\n<b>Alarm:</b> {row['Standard_Alarm_Name']}\n<b>Time:</b> {row['OpenTime']}\n<b>TT No:</b> {row['TTNumber']}"

        if not pd.isna(row['CE Chat ID']):
            send_telegram_message(int(row['CE Chat ID']), msg)

# --- Run Script ---
if __name__ == "__main__":
    escalate_alarms()
