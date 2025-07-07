import os
import sys
import logging
import streamlit as st
import pandas as pd

# Fix import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.preprocessor import load_and_preprocess_alarm_file
from telegram_bot.escalate_alarms import escalate_alarms
from mongodb.mongo_crud import insert_bulk_alarms
from automation.download_and_preprocess import download_alarm_log, get_latest_downloaded_file
from utils.mongo_utils import df_to_dicts

# Constants
DOWNLOAD_DIR = os.path.abspath("data/raw")
PROCESSED_OUTPUT = "data/processed/cleaned_alarms.csv"
ESCALATION_MATRIX_FILE = "data/reference/Alarm_Escalation_Matrix.xlsx"
COLLECTION_NAME = "AlarmLogs"

# UI
st.title("🚨 Alarm Automation Dashboard")
uploaded_file = st.file_uploader("📤 Upload Alarm Log File", type=["xlsx", "csv"])

# Trigger: Download or use uploaded file
if st.button("⚙️ Preprocess & Upload to MongoDB"):
    st.info("🔄 Processing started...")
    if uploaded_file is not None:
        uploaded_path = os.path.join(DOWNLOAD_DIR, uploaded_file.name)
        with open(uploaded_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"📂 Uploaded file saved: {uploaded_file.name}")
        source_file = uploaded_path
    else:
        st.info("📥 Downloading file from portal...")
        if not download_alarm_log():
            st.error("❌ Failed to download alarm file.")
            st.stop()
        source_file = get_latest_downloaded_file(DOWNLOAD_DIR)
        if not source_file:
            st.error("❌ No downloaded file found.")
            st.stop()
        st.success(f"✅ Downloaded file: {os.path.basename(source_file)}")

    # Preprocess and upload
    try:
        df = load_and_preprocess_alarm_file(source_file, PROCESSED_OUTPUT)
        st.success("✅ Preprocessing complete.")

        records = df_to_dicts(df)
        insert_bulk_alarms(records, COLLECTION_NAME)
        st.success("✅ Data inserted into MongoDB.")
    except Exception as e:
        st.error(f"❌ Error during processing: {e}")

# Trigger: Escalation
if st.button("📣 Escalate Alarms via Telegram"):
    try:
        escalate_alarms(PROCESSED_OUTPUT, ESCALATION_MATRIX_FILE)
        st.success("📢 Telegram alarm escalation completed.")
    except Exception as e:
        st.error(f"❌ Escalation failed: {e}")
