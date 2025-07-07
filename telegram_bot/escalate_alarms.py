import pandas as pd
import logging
import requests
from datetime import datetime

TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"
BOT_TOKEN = "7024693642:AAHgmr1ttNQJr2X299vtjMcxSDfc60zfiNk"
LONG_PENDING_THRESHOLD_MINUTES = 60

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def escape_markdown(text):
    import re
    if pd.isna(text):
        return ""
    return re.sub(r'([*_`\[\]()~>#+=|{}.!-])', r'\\\1', str(text))

def send_grouped_by_site(chat_id, role, alarms_df):
    if alarms_df.empty:
        return

    grouped = alarms_df.groupby(["GLOBAL_ID", "SITE_NAME"])
    header = f"🔔 *{role} Alarm Escalation*\nTotal Sites: {len(grouped)}\n\n"

    max_len = 4000  # Telegram safe limit
    message = header
    messages = []

    for (site_id, site_name), group in grouped:
        site_block = (
            f"📍 *Site ID:* {escape_markdown(site_id)}\n"
            f"🏠 *Site Name:* {escape_markdown(site_name)}\n"
            f"📡 *Operator:* {escape_markdown(group.iloc[0].get('SourceInput', 'Unknown'))}\n"
        )
        for _, row in group.iterrows():
            site_block += (
                f"  • *Alarm:* {escape_markdown(row.get('EventName'))}\n"
                f"    🕐 {escape_markdown(row.get('OpenTime'))}\n"
            )
        site_block += "---\n"

        if len(message + site_block) > max_len:
            messages.append(message)
            message = header + site_block  # Start new message with header
        else:
            message += site_block

    messages.append(message)  # Append final message

    for msg in messages:
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }
        response = requests.post(TELEGRAM_API_URL.format(BOT_TOKEN), data=payload)
        if response.status_code != 200:
            logging.error(f"Failed to send message to {chat_id}: {response.text}")
        else:
            logging.info(f"✅ Message sent to {chat_id} for {role}.")


def escalate_alarms(cleaned_alarm_file, escalation_matrix_file):
    alarms_df = pd.read_csv(cleaned_alarm_file)
    escalation_df = pd.read_excel(escalation_matrix_file)

    # Normalize column names
    escalation_df.columns = escalation_df.columns.str.strip().str.replace(" ", "_")
    alarms_df.columns = alarms_df.columns.str.strip().str.replace(" ", "_")

    # Ensure ID columns are string
    alarms_df["SiteID"] = alarms_df["SiteID"].astype(str)
    escalation_df["GLOBAL_ID"] = escalation_df["GLOBAL_ID"].astype(str)

    # Merge
    merged_df = pd.merge(alarms_df, escalation_df, left_on="SiteID", right_on="GLOBAL_ID", how="left")

    # Convert OpenTime to datetime
    now = datetime.now()
    merged_df["OpenTime"] = pd.to_datetime(merged_df["OpenTime"], errors="coerce")
    merged_df["PendingMinutes"] = (now - merged_df["OpenTime"]).dt.total_seconds() / 60

    # === Escalate to Technician ===
    tech_groups = merged_df.groupby("Technician_Chat_id")
    for chat_id, group in tech_groups:
        if pd.notna(chat_id):
            send_grouped_by_site(int(chat_id), "Technician", group)

    # === Escalate to Supervisor ===
    sup_groups = merged_df.groupby("Supervisor_Chat_ID")
    for chat_id, group in sup_groups:
        if pd.notna(chat_id):
            send_grouped_by_site(int(chat_id), "Supervisor", group)

    # === Escalate long-pending to CE ===
    long_pending = merged_df[merged_df["PendingMinutes"] > LONG_PENDING_THRESHOLD_MINUTES]
    ce_groups = long_pending.groupby("CE_Chat_ID")
    for chat_id, group in ce_groups:
        if pd.notna(chat_id):
            send_grouped_by_site(int(chat_id), "Cluster Engineer", group)
