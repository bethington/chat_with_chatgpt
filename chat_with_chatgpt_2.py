import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import undetected_chromedriver as uc
from fake_useragent import UserAgent
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import threading

# Load environment variables from .env file
load_dotenv()

# Setup logging for better traceability
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants (ensure these are correctly set in your .env file)
MAIL = os.getenv('MAIL')
PASSWORD = os.getenv('PASSWORD')
CHROME_BINARY_LOCATION = os.getenv('CHROME_BINARY_LOCATION')
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')
CHATGPT_URL = 'https://chat.openai.com/'  # Corrected URL
COOKIES_PATH = "cookies.pkl"

# Initialize Flask app
app = Flask(__name__)

def save_cookies(driver, path):
    """Save cookies to a file.

    Args:
        driver (_type_): _description_
        path (_type_): _description_
    """
    with open(path, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)
    logging.info(f"Cookies saved to {path}")

def load_cookies(driver, path):
    """Load cookies from a file.

    Args:
        driver (_type_): _description_
        path (_type_): _description_
    """
    with open(path, 'rb') as cookiesfile:
        cookies = pickle.load(cookiesfile)
        for cookie in cookies:
            # Selenium expects expiry to be an int
            if isinstance(cookie.get('expiry', None), float):
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
    logging.info(f"Cookies loaded from {path}")

def setup_driver():
    """Load cookies from a file.

    Returns:
        _type_: _description_
    """
    chrome_options = webdriver.ChromeOptions()
    # Uncomment and set user-agent or user-data-dir if needed
    # chrome_options.add_argument(f"user-agent={UserAgent().random}")
    # chrome_options.add_argument(r"user-data-dir=C:\\Users\\benam\\AppData\\Local\\Google\\Chrome\\User Data")
    # chrome_options.add_experimental_option("detach", True)
    # chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.binary_location = CHROME_BINARY_LOCATION
    
    logging.info("Starting Chrome browser")
    try:
        driver = uc.Chrome(options=chrome_options, driver_executable_path=CHROME_DRIVER_PATH)
    except Exception as e:
        logging.error(f"Error initializing Chrome driver: {e}")
        return None
    sleep(5)  # Reduced sleep time; using explicit waits is better
    
    # Open the ChatGPT website
    try:
        driver.get(CHATGPT_URL)
        logging.info(f"Navigated to {CHATGPT_URL}")
    except Exception as e:
        logging.error(f"Error navigating to {CHATGPT_URL}: {e}")
        driver.quit()
        return None
    sleep(5)  # Allow time for page to load
    
    # Attempt to load cookies if they exist
    if os.path.exists(COOKIES_PATH):
        logging.info("Loading cookies from file")
        try:
            load_cookies(driver, COOKIES_PATH)
            driver.refresh()  # Refresh to apply cookies
            logging.info("Cookies loaded and page refreshed")
            sleep(5)  # Wait for the page to load after refresh
        except Exception as e:
            logging.error(f"Error loading cookies: {e}")
    
    # Click login button
    try:
        loginBtn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='login-button']"))
        )
        loginBtn.click()
        logging.info("Clicked login button")
    except Exception as e:
        logging.error(f"Error clicking login button: {e}")
        driver.quit()
        return None
    sleep(3)
    
    # Enter email
    try:
        emailInput = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='email-input']"))  # Updated XPath
        )
        emailInput.send_keys(MAIL) # type: ignore
        logging.info("Entered email")
    except Exception as e:
        logging.error(f"Error entering email: {e}")
        driver.quit()
        return None
    sleep(3)
    
    # Click continue
    try:
        continueBtn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='continue-btn']"))  # Updated XPath
        )
        continueBtn.click()
        logging.info("Clicked continue button")
    except Exception as e:
        logging.error(f"Error clicking continue button: {e}")
        driver.quit()
        return None
    sleep(3)
    
    # Enter password
    try:
        passwordInput = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='password']"))
        )
        passwordInput.send_keys(PASSWORD) # type: ignore
        logging.info("Entered password")
    except Exception as e:
        logging.error(f"Error entering password: {e}")
        driver.quit()
        return None
    sleep(3)
    
    # Submit the login form
    try:
        submitBtn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        submitBtn.click()
        logging.info("Clicked submit button")
    except Exception as e:
        logging.error(f"Error clicking submit button: {e}")
        driver.quit()
        return None
    sleep(10)
    
    # Wait until the prompt input is present, indicating successful login
    try:
        promptInput = WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='prompt-textarea']"))  # Updated XPath
        )
        if promptInput:
            logging.info("Login successful")
            save_cookies(driver, COOKIES_PATH)  # Save cookies after successful login
    except Exception as e:
        logging.error(f"Error during post-login wait: {e}")
        driver.quit()
        return None
    
    return driver

# Initialize the Selenium driver
driver = setup_driver()
if not driver:
    logging.error("Failed to initialize the Selenium driver. Exiting.")
    exit(1)

# Lock to ensure that only one request is processed at a time
lock = threading.Lock()

@app.route('/process_prompt', methods=['POST'])
def process_prompt():
    """Process a user-provided prompt and return the AI response.

    Returns:
        _type_: _description_
    """
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({'error': 'No prompt provided'}), 400
    
    user_prompt = data['prompt']
    logging.info(f"Received prompt: {user_prompt}")
    
    with lock:
        try:
            # Locate the prompt input area
            promptInput = WebDriverWait(driver, 30).until( # type: ignore
                EC.presence_of_element_located((By.XPATH, "//div[@id='prompt-textarea']"))  # Updated XPath
            )
            
            # Clear any existing text (if necessary)
            promptInput.clear()
            
            # Enter the user's prompt
            promptInput.send_keys(user_prompt)
            logging.info("Entered user prompt")
            sleep(1)  # Small delay to ensure text is entered
            
            # Send the prompt
            promptBtn = WebDriverWait(driver, 30).until( # type: ignore
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='send-button']"))
            )
            promptBtn.click()
            logging.info("Clicked send button")
            sleep(5)
            
            # Wait for ai to respond
            logging.info("Waiting for response to finish...")
            promptBtn = WebDriverWait(driver, 120).until( # type: ignore
                EC.presence_of_element_located((By.XPATH, "//button[@data-testid='send-button']"))
            )
            logging.info("Response complete")
            
            # Wait for the response to appear
            logging.info("Waiting for responses to appear...")
            articles = WebDriverWait(driver, 30).until( # type: ignore
                EC.presence_of_all_elements_located((By.CLASS_NAME, "markdown"))  # Updated XPath
            )
            logging.info("Responses visible")
            
            # Assuming the latest response is the last article
            if len(articles) < 1:
                return jsonify({'error': 'No response received'}), 500
            
            response_text = articles[-1].text  # Get the latest response
            response_html = articles[-1].get_attribute("innerHTML")  # Get the latest response
            logging.info(f"Received response: {response_text}")
            
            return jsonify({'responseText': response_text, 'responseHtml': response_html}), 200
        
        except Exception as e:
            logging.error(f"Error processing prompt: {e}")
            return jsonify({'error': 'Failed to process prompt'}), 500

# Adding the /test endpoint for testing purposes
@app.route('/test', methods=['POST'])
def test_endpoint():
    """A simple test endpoint that returns a Hello World message.
    This can be used to verify that the Flask server is running correctly.

    Returns:
        _type_: _description_
    """
    return jsonify({'message': 'Hello World'}), 200

def run_flask():
    """Run the Flask app.
    """
    # Run Flask app on a separate thread to prevent blocking
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Start the Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logging.info("Flask server is running and waiting for POST requests...")
    
    # Keep the main thread alive to maintain the Selenium session
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        driver.quit()
        exit(0)
