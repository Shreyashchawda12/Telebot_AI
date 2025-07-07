import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import logging
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Import your preprocessing function
from utils.preprocessor import load_and_preprocess_alarm_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DOWNLOAD_DIR = os.path.abspath("data/raw")
PROCESSED_OUTPUT = "data/processed/cleaned_alarms.csv"

USERNAME = "MH_jitendra_Sahoo"
PASSWORD = "Altius@123"

def setup_driver(download_dir):
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    # chrome_options.add_argument("--headless")  # optional
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def wait_for_element(driver, locator, timeout=20, condition=EC.presence_of_element_located):
    return WebDriverWait(driver, timeout).until(condition(locator))

def download_alarm_log():
    driver = setup_driver(DOWNLOAD_DIR)
    try:
        logging.info("Opening login page.")
        driver.get("https://vnoc.atctower.in/vnoc/Default.aspx")

        wait_for_element(driver, (By.NAME, 'appLogin$UserName')).send_keys(USERNAME)
        driver.find_element(By.NAME, 'appLogin$Password').send_keys(PASSWORD)
        driver.find_element(By.NAME, 'appLogin$LoginImageButton').click()

        wait_for_element(driver, (By.ID, 'ctl00_Html1'))  # Post-login page

        logging.info("Navigating to TT Log page.")
        driver.get("https://vnoc.atctower.in/vnoc/aspx/TroubleTicketLogDetail.aspx")
        wait_for_element(driver, (By.ID, 'aspnetForm'))

        # Wait for any loading screen
        WebDriverWait(driver, 60).until(
            EC.invisibility_of_element_located((By.XPATH, "//*[contains(text(),'Loading....')]"))
        )

        # Open grid menu
        logging.info("Clicking grid menu.")
        grid_menu_button = wait_for_element(driver, 
            (By.CSS_SELECTOR, "div[role='button'][id*='grid-menu']"),
            condition=EC.element_to_be_clickable
        )
        ActionChains(driver).move_to_element(grid_menu_button).click().perform()
        time.sleep(1)

        # Find and click "Download as Excel"
        menu_items = driver.find_elements(By.CSS_SELECTOR, ".ui-grid-menu .menu-item")
        logging.info(f"Found {len(menu_items)} menu items:")
        for item in menu_items:
            logging.info(f"Menu item found: '{item.text.strip()}'")
            if "Excel" in item.text:
                logging.info("✅ Found a match! Clicking it.")
                item.click()
                break
        else:
            logging.warning("❌ No menu item with 'Excel' found.")


        time.sleep(60)  # wait for file to download
        logging.info("Download complete.")
        return True

    except Exception as e:
        logging.error(f"Download failed: {e}")
        return None

    finally:
        driver.quit()

def get_latest_downloaded_file(folder):
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".xlsx")]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

if __name__ == "__main__":
    logging.info("Starting automated alarm log download and preprocessing.")
    
    if download_alarm_log():
        latest_file = get_latest_downloaded_file(DOWNLOAD_DIR)
        if latest_file:
            logging.info(f"Latest file: {latest_file}")
            df = load_and_preprocess_alarm_file(latest_file, PROCESSED_OUTPUT)
        else:
            logging.warning("No Excel file found in download folder.")
    else:
        logging.error("Alarm log download failed.")
