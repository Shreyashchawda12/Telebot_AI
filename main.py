import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from utils.preprocessor import load_and_preprocess_alarm_file
from telegram_bot.escalate_alarms import escalate_alarms
from mongodb.mongo_crud import insert_bulk_alarms
from automation.download_and_preprocess import download_alarm_log, get_latest_downloaded_file
from utils.mongo_utils import df_to_dicts
import asyncio

# Constants
DOWNLOAD_DIR = os.path.abspath("data/raw")
PROCESSED_OUTPUT = "data/processed/cleaned_alarms.csv"
ESCALATION_MATRIX_FILE = "data/reference/Alarm_Escalation_Matrix.xlsx"
COLLECTION_NAME = "AlarmLogs"

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    logging.info("🚀 Starting Alarm Automation Process")

    if download_alarm_log():
        latest_file = get_latest_downloaded_file(DOWNLOAD_DIR)

        if latest_file:
            logging.info(f"✅ Found latest file: {latest_file}")

            # Step 1: Preprocess
            df = load_and_preprocess_alarm_file(latest_file, PROCESSED_OUTPUT)
            logging.info(f"✅ Preprocessing completed. Cleaned file saved to: {PROCESSED_OUTPUT}")

            # Step 2: Escalate
            escalate_alarms(PROCESSED_OUTPUT, ESCALATION_MATRIX_FILE)
            logging.info("📢 Telegram alarm escalation completed.")

            # Step 3: Upload to MongoDB
            records = df_to_dicts(df)
            asyncio.run(insert_bulk_alarms(records, COLLECTION_NAME))
            logging.info("✅ Alarms uploaded to MongoDB.")

        else:
            logging.warning("⚠ No alarm log file found.")
    else:
        logging.error("❌ Alarm log download failed.")


if __name__ == "__main__":
    main()
