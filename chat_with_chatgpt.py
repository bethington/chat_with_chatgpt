import os
import pandas as pd
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import undetected_chromedriver as uc
from fake_useragent import UserAgent
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging for better traceability
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants (move sensitive data like this to environment variables for security in real apps)
MAIL = os.getenv('MAIL')
PASSWORD = os.getenv('PASSWORD')
CHROME_BINARY_LOCATION = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
CHROMEDRIVER_PATH = "C:\\Users\\benam\\source\\chromedriver-win64\\chromedriver.exe"
CHATGPT_URL = 'https://chatgpt.com/'
COOKIES_PATH = "cookies.pkl"
# PROMPT = "Give a summary of the life and work of Albert Einstein."
PROMPT =  "Using attached Python code add functionality to wait for chrome browser to load before continuing."

def save_cookies(driver, path):
    """Save cookies to a file."""
    with open(path, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)
    logging.info(f"Cookies saved to {path}")

def load_cookies(driver, path):
    """Load cookies from a file."""
    with open(path, 'rb') as cookiesfile:
        cookies = pickle.load(cookiesfile)
        for cookie in cookies:
            # Selenium expects expiry to be an int
            if isinstance(cookie.get('expiry', None), float):
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
    logging.info(f"Cookies loaded from {path}")

# Set up Chrome options
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument(f"user-agent={UserAgent.random}")
# chrome_options.add_argument(r"user-data-dir=C:\\Users\\benam\\AppData\\Local\\Google\\Chrome\\User Data")
# chrome_options.add_experimental_option("detach", True)
# chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_options.binary_location = CHROME_BINARY_LOCATION

# Start the Chrome driver
logging.info("Starting Chrome browser")
driver = uc.Chrome(options=chrome_options)
sleep(3)

# Open the ChatGPT website
driver.get(CHATGPT_URL)
sleep(3)

# Attempt to load cookies if they exist
if os.path.exists(COOKIES_PATH):
    logging.info("Loading cookies from file")
    try:
        load_cookies(driver, COOKIES_PATH)
        driver.refresh()  # Refresh to apply cookies
        sleep(5)  # Wait for the page to load after refresh
    except Exception as e:
        logging.error(f"Error loading cookies: {e}")

# Click login button
loginBtn = driver.find_element(By.XPATH, "//button[@data-testid='login-button']")
loginBtn.click()
sleep(3)

# Enter email
emailInput = driver.find_element(By.XPATH,"//input[@id='email-input']")
emailInput.send_keys(MAIL)
sleep(3)

# Click continue
continueBtn = driver.find_element(By.XPATH, "//button[@class='continue-btn']")
continueBtn.click()
sleep(3)

# Enter password
password = driver.find_element(By.XPATH, "//input[@id='password']")
password.send_keys(PASSWORD)
sleep(3)

# Submit the login form
submitBtn = driver.find_element(By.XPATH, "//button[@type='submit']")
submitBtn.click()
sleep(10)

# Wait until the prompt input is present, indicating successful login
try:
   wait = WebDriverWait(driver, 120)
   promptInput = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='prompt-textarea']")))
   if promptInput:
      logging.info("Login successful")
      save_cookies(driver, COOKIES_PATH)  # Save cookies after successful login
except Exception as e:
   logging.error(f"Error during post-login wait: {e}")
   driver.quit()

# Enter the prompt
promptInput = driver.find_element(By.XPATH, "//div[@id='prompt-textarea']")
promptInput.send_keys(PROMPT)
sleep(3)

# Send the prompt
promptBtn = driver.find_element(By.XPATH, "//button[@data-testid='send-button']")
promptBtn.click()
sleep(10)

# Capture the output
articleOutput = driver.find_elements(By.XPATH, "//article")
print(articleOutput[1].text)
sleep(5)