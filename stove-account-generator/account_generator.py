import os
import sys
import random
import string
import json
import time
from datetime import datetime
from typing import Dict, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    NoSuchElementException,
    WebDriverException
)
from email_handler import TempMailHandler
from selenium.webdriver.common.action_chains import ActionChains
import re

class CrossfireAccountGenerator:
    def __init__(self, use_proxy: bool = False, proxy: Optional[str] = None, max_retries: int = 3, password_length: int = 12, email_service: str = 'yopmail.com'):
        # Environment setup
        os.environ['WDM_LOG_LEVEL'] = '0'
        os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
        os.environ['PATH'] = os.environ['PATH'] + r';C:\Program Files\Google\Chrome\Application'
        os.environ['UC_DOWNLOAD_TIMEOUT'] = '30'
        os.environ['UC_CONNECT_TIMEOUT'] = '30'
        
        self.base_url = "https://accounts.onstove.com"
        self.proxy = proxy
        self.max_retries = max_retries
        self.driver = self._setup_driver(use_proxy)
        self.accounts_file = "generated_accounts.json"
        self.used_emails = set()  # Track used emails
        self.password_length = min(max(password_length, 8), 15)  # Ensure length is between 8 and 15
        
        # Initialize email handler based on service selection
        print(f"Initializing with email service: {email_service}")
        if email_service == '10minutemail.net':
            from tempmail_handler import TempMailOrgHandler
            self.email_handler = TempMailOrgHandler(driver=self.driver)
        else:
            # Default to yopmail.com
            from email_handler import TempMailHandler
            self.email_handler = TempMailHandler(driver=self.driver)
        
    def _setup_driver(self, use_proxy: bool) -> uc.Chrome:
        print("Starting Chrome driver setup...")
        options = uc.ChromeOptions()
        
        # Basic options
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        print("Chrome options configured...")
        
        if use_proxy and self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        
        try:
            print("Attempting to create Chrome driver...")
            # Use local chromedriver for Stove
            chromedriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver.exe")
            if getattr(sys, 'frozen', False):
                chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
            
            # Create driver without headless option
            driver = uc.Chrome(
                options=options,
                driver_executable_path=chromedriver_path,
                version_main=133,  # Make sure this matches your Chrome version
                use_subprocess=True
            )
            print("Chrome driver created successfully!")
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            return driver
            
        except Exception as e:
            print(f"Failed to create Chrome driver: {str(e)}")
            print("Chrome setup error details:")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_random_credentials(self) -> Dict[str, str]:
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        
        # Calculate number of characters for each category
        remaining_length = self.password_length - 4  # Reserve space for required characters
        lowercase_count = max(1, remaining_length // 2)
        uppercase_count = max(1, (remaining_length - lowercase_count) // 2)
        numbers_count = max(1, remaining_length - lowercase_count - uppercase_count)
        
        # Generate parts of password
        lowercase = ''.join(random.choices(string.ascii_lowercase, k=lowercase_count))
        uppercase = ''.join(random.choices(string.ascii_uppercase, k=uppercase_count))
        numbers = ''.join(random.choices(string.digits, k=numbers_count))
        special = random.choice('!@#$%^&*')
        
        # Combine all parts and shuffle
        password_chars = list(lowercase + uppercase + numbers + special)
        random.shuffle(password_chars)
        password = ''.join(password_chars)
        
        return {
            "username": username,
            "password": password,
            "email": username + "@temporary-mail.net"  # This will be replaced by temp-mail.org email
        }
    
    def human_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add random delay to simulate human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def safe_click(self, element, retries: int = 3) -> bool:
        """Safely click an element with retries"""
        for attempt in range(retries):
            try:
                self.human_delay(0.5, 1.0)
                try:
                    element.click()
                except:
                    # Try JavaScript click if regular click fails
                    self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Failed to click element after {retries} attempts: {str(e)}")
                    return False
                time.sleep(1)
        return False

    def safe_send_keys(self, element, text: str, retries: int = 3) -> bool:
        """Safely send keys to an element with retries"""
        for attempt in range(retries):
            try:
                element.clear()
                for char in text:
                    element.send_keys(char)
                    self.human_delay(0.05, 0.1)  # Simulate human typing
                return True
            except (StaleElementReferenceException, NoSuchElementException) as e:
                if attempt == retries - 1:
                    print(f"Failed to send keys after {retries} attempts: {str(e)}")
                    return False
                time.sleep(1)
        return False

    def create_account(self, credentials: Optional[Dict[str, str]] = None, verification_handler=None) -> bool:
        try:
            # Initialize email handler if needed
            if not hasattr(self, 'email_handler'):
                self.email_handler = TempMailHandler()

            # Create temporary email (passing used emails set)
            temp_email = self.email_handler.create_email(self.used_emails)
            if not temp_email:
                raise Exception("Failed to create temporary email")

            if not credentials:
                # Create temp email first
                credentials = self.generate_random_credentials()
                credentials['email'] = temp_email

            # 1. Start at signup page directly
            print("Navigating to signup page...")
            self.driver.get("https://accounts.onstove.com/signup")
            self.human_delay(2, 3)
            
            # 2. Click "Sign up with email" button
            print("Clicking 'Sign up with email' button...")
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if "email" in button.text.lower():
                        print("Found email signup button")
                        self.driver.execute_script("arguments[0].click();", button)
                        break
            except Exception as e:
                print(f"Error clicking email button: {str(e)}")
                raise
            
            self.human_delay(2, 3)
            
            # 3. Fill Date of Birth
            print("Filling date of birth...")
            current_year = datetime.now().year
            birth_year = current_year - random.randint(18, 60)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            
            try:
                # Wait for the date input field to be present
                print("Waiting for date input field...")
                dob_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                )
                
                # Format date string as MM.DD.YYYY
                dob_string = f"{birth_month:02d}.{birth_day:02d}.{birth_year}"
                print(f"Entering date of birth: {dob_string}")
                
                # Clear the field first
                dob_input.clear()
                self.human_delay(0.5, 1)
                
                # Send keys with explicit formatting
                dob_input.send_keys(dob_string)
                self.human_delay(1, 2)
                
                # Click Next button
                print("Clicking Next button...")
                try:
                    # Try multiple selectors for the Next button
                    selectors = [
                        "button.stds-button.stds-button-primary",
                        "button.stds-button",
                        "button[type='button']",
                        "//button[contains(@class, 'stds-button')]"
                    ]
                    
                    next_button = None
                    for selector in selectors:
                        try:
                            if selector.startswith("//"):
                                next_button = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                            else:
                                next_button = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                            if next_button:
                                break
                        except:
                            continue
                    
                    if next_button:
                        print("Found Next button, clicking...")
                        self.driver.execute_script("arguments[0].click();", next_button)
                        self.human_delay(2, 3)
                    else:
                        raise Exception("Could not find Next button")
                    
                except Exception as e:
                    print(f"Error clicking Next button: {str(e)}")
                    raise
                
                # 5. Handle Terms Agreement
                print("Accepting terms...")
                try:
                    # Wait for checkboxes to be present
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='checkbox']"))
                    )
                    
                    # Find and click "Agree to all" checkbox first
                    agree_all = self.driver.find_element(By.XPATH, "//label[contains(., 'Agree to all')]")
                    self.driver.execute_script("arguments[0].click();", agree_all)
                    self.human_delay(1, 2)
                    
                    # Verify all checkboxes are checked
                    checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                    for checkbox in checkboxes:
                        if not checkbox.is_selected():
                            label = checkbox.find_element(By.XPATH, "./following-sibling::label")
                            self.driver.execute_script("arguments[0].click();", label)
                            self.human_delay(0.5, 1)
                    
                    # Click "Agree and continue" button - trying multiple selectors
                    print("Clicking Agree and continue button...")
                    button_selectors = [
                        "button.stds-button.stds-button-primary",
                        "//button[contains(@class, 'stds-button-primary')]",
                        "//button[contains(text(), 'Agree and continue')]",
                        "//button[contains(@class, 'stds-button') and contains(text(), 'continue')]",
                        "//div[contains(@class, 'stds-actions')]//button"
                    ]
                    
                    agree_continue_button = None
                    for selector in button_selectors:
                        try:
                            if selector.startswith("//"):
                                agree_continue_button = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                            else:
                                agree_continue_button = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                            if agree_continue_button:
                                print(f"Found button with selector: {selector}")
                                break
                        except:
                            continue
                    
                    if agree_continue_button:
                        # Try multiple click methods
                        try:
                            # Method 1: Regular click
                            agree_continue_button.click()
                        except:
                            try:
                                # Method 2: JavaScript click
                                self.driver.execute_script("arguments[0].click();", agree_continue_button)
                            except:
                                # Method 3: Action chains
                                actions = ActionChains(self.driver)
                                actions.move_to_element(agree_continue_button).click().perform()
                        
                        print("Clicked Agree and continue button")
                        self.human_delay(2, 3)
                    else:
                        raise Exception("Could not find Agree and continue button")
                    
                except Exception as e:
                    print(f"Error handling terms agreement: {str(e)}")
                    # Take screenshot for debugging
                    self.driver.save_screenshot("error_screenshot.png")
                    print("Screenshot saved as error_screenshot.png")
                    raise
                
                # 6. Fill Registration Form
                print("Filling registration form...")
                try:
                    # Wait for email field and fill it
                    email_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                    )
                    print(f"Entering email: {credentials['email']}")
                    self.safe_send_keys(email_input, credentials["email"])
                    self.human_delay(1, 2)
                    
                    # Click Send Verification Email button
                    print("Clicking Send Verification Email button...")
                    send_verification_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.stds-button-primary"))
                    )
                    self.safe_click(send_verification_button)
                    
                    # After clicking Send Verification Email button
                    print("Waiting for CAPTCHA completion...")
                    if verification_handler:
                        if not verification_handler():
                            raise Exception("CAPTCHA verification timed out or was cancelled")
                    else:
                        input("Press Enter after completing the CAPTCHA...")
                    
                    # Get verification code automatically
                    verification_code = None
                    for attempt in range(3):  # Try 3 times to get the code
                        print(f"Attempt {attempt + 1} to get verification code...")
                        verification_code = self.email_handler.wait_for_verification_code()
                        if verification_code:
                            break
                        time.sleep(5)  # Wait between attempts
                    
                    if not verification_code:
                        raise Exception("Could not get verification code after 3 attempts")
                    
                    # After entering verification code
                    try:
                        # Wait for verification input field
                        verification_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "input[maxlength='6']"))
                        )
                        
                        # Human-like typing of verification code
                        print("Entering verification code...")
                        verification_input.click()
                        self.human_delay(0.3, 0.7)
                        
                        # Type each digit with human-like delays
                        for digit in verification_code:
                            verification_input.send_keys(digit)
                            self.human_delay(0.1, 0.3)
                        
                        print("Verification code entered")
                        if verification_handler:
                            verification_handler()
                        else:
                            print("\n=== Please click the 'Confirm Verification Code' button manually ===")
                            input("Press Enter after clicking the confirm button...")
                        
                        # Wait for verification to be successful by checking if field is disabled
                        try:
                            WebDriverWait(self.driver, 10).until(
                                lambda driver: (
                                    # Check if verification field is disabled
                                    "disabled" in verification_input.get_attribute("class") or
                                    not verification_input.is_enabled() or
                                    # Check if verification complete message appears
                                    len(driver.find_elements(By.CSS_SELECTOR, ".verification-complete")) > 0 or
                                    # Check if password fields appear
                                    len(driver.find_elements(By.CSS_SELECTOR, "input[type='password']")) > 0
                                )
                            )
                            print("Verification successful - field is disabled")

                            # After verification is successful
                            print("Verification successful - proceeding with password")

                            # Wait for password fields
                            try:
                                # Wait for password fields to appear
                                print("Waiting for password fields...")
                                password_fields = WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='password']"))
                                )
                                
                                if len(password_fields) >= 2:
                                    # Fill first password field
                                    print("Entering password...")
                                    self.safe_send_keys(password_fields[0], credentials["password"])
                                    self.human_delay(0.5, 1.0)
                                    
                                    # Fill confirm password field
                                    print("Confirming password...")
                                    self.safe_send_keys(password_fields[1], credentials["password"])
                                    self.human_delay(0.5, 1.0)
                                    
                                    # After password fields are filled
                                    print("Looking for Next button...")
                                    try:
                                        # Try multiple selectors for the Next button
                                        next_button_selectors = [
                                            "button.w-full.stds-button.stds-button-primary",
                                            "button.stds-button.stds-button-primary",
                                            "button[type='button']",
                                            "//button[contains(@class, 'w-full')]",
                                            "//button[contains(@class, 'stds-button-primary')]"
                                        ]
                                        
                                        next_button = None
                                        for selector in next_button_selectors:
                                            try:
                                                if selector.startswith("//"):
                                                    next_button = WebDriverWait(self.driver, 5).until(
                                                        EC.element_to_be_clickable((By.XPATH, selector))
                                                    )
                                                else:
                                                    next_button = WebDriverWait(self.driver, 5).until(
                                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                    )
                                                if next_button:
                                                    print(f"Found Next button using selector: {selector}")
                                                    break
                                            except:
                                                continue
                                        
                                        if next_button:
                                            # Try multiple click methods
                                            try:
                                                # Method 1: Regular click
                                                next_button.click()
                                            except:
                                                try:
                                                    # Method 2: JavaScript click
                                                    self.driver.execute_script("arguments[0].click();", next_button)
                                                except:
                                                    # Method 3: Action chains
                                                    actions = ActionChains(self.driver)
                                                    actions.move_to_element(next_button)
                                                    actions.click()
                                                    actions.perform()
                                            
                                            print("Clicked Next button")
                                            self.human_delay(1, 2)
                                        else:
                                            raise Exception("Could not find Next button after password entry")
                                        
                                    except Exception as e:
                                        print(f"Error clicking Next button: {str(e)}")
                                        self.driver.save_screenshot("next_button_error.png")
                                        raise

                            except Exception as e:
                                print(f"Error during password entry: {str(e)}")
                                self.driver.save_screenshot("password_error.png")
                                raise

                        except TimeoutException:
                            print("Verification failed - field still enabled")
                            raise Exception("Verification failed - field not disabled")

                    except Exception as e:
                        print(f"Error during verification: {str(e)}")
                        self.driver.save_screenshot("verification_error.png")
                        raise

                except Exception as e:
                    print(f"Error in registration form: {str(e)}")
                    self.driver.save_screenshot("error_screenshot.png")
                    raise
                
            except Exception as e:
                print(f"Error filling date of birth: {str(e)}")
                raise
            
            # After clicking Next button on password page
            print("Waiting for completion page...")
            try:
                # Wait for completion page with shorter timeout and multiple checks
                completion_found = False
                max_attempts = 3
                timeout = 5  # Reduced timeout per attempt
                
                for attempt in range(max_attempts):
                    try:
                        # Try multiple ways to verify completion
                        WebDriverWait(self.driver, timeout).until(
                            lambda driver: any([
                                "signup/completed" in driver.current_url,
                                driver.find_elements(By.CSS_SELECTOR, "button.relative.w-full.stds-button.stds-button-primary"),  # Start STOVE button
                                driver.find_elements(By.CSS_SELECTOR, ".text-primary")  # STOVE ID element
                            ])
                        )
                        completion_found = True
                        break
                    except:
                        print(f"Completion check attempt {attempt + 1}/{max_attempts}...")
                        continue
                
                if not completion_found:
                    raise Exception("Could not verify completion page")
                
                print("Successfully reached completion page")
                self.human_delay(1, 2)  # Reduced delay
                
                # Get STOVE ID quickly using multiple selectors
                try:
                    stove_id = None
                    selectors = [
                        ".text-primary",
                        "span[class*='text-primary']",
                        "div[class*='text-primary']",
                        "//span[contains(text(), 'S1')]",
                        "//div[contains(text(), 'S1')]"
                    ]
                    
                    for selector in selectors:
                        try:
                            if selector.startswith("//"):
                                element = self.driver.find_element(By.XPATH, selector)
                            else:
                                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                            if element:
                                text = element.text.strip()
                                if text.startswith("S1"):
                                    stove_id = text
                                    print(f"Found STOVE ID: {stove_id}")
                                    break
                        except:
                            continue
                    
                    if not stove_id:
                        raise Exception("Could not find STOVE ID")
                    
                    # Quick save to both files
                    try:
                        # Ensure the account data is properly formatted
                        account_data = {
                            "email": str(credentials["email"]).strip(),
                            "password": str(credentials["password"]).strip(),
                            "stove_id": str(stove_id).strip(),
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "last_used": "Never",
                            "status": "Active"
                        }
                        
                        # Save to JSON file with proper encoding and error handling
                        try:
                            # Create backup of existing file if it exists
                            if os.path.exists(self.accounts_file):
                                backup_file = f"{self.accounts_file}.bak"
                                try:
                                    with open(self.accounts_file, 'r', encoding='utf-8') as src:
                                        with open(backup_file, 'w', encoding='utf-8') as dst:
                                            dst.write(src.read())
                                except Exception as e:
                                    print(f"Warning: Could not create backup: {str(e)}")
                            
                            # Load existing accounts or create new list
                            try:
                                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                                    accounts = json.load(f)
                                    if not isinstance(accounts, list):
                                        accounts = []
                            except (FileNotFoundError, json.JSONDecodeError):
                                accounts = []
                            
                            # Add new account and save
                            accounts.append(account_data)
                            
                            # Save with temporary file to prevent corruption
                            temp_file = f"{self.accounts_file}.tmp"
                            with open(temp_file, 'w', encoding='utf-8') as f:
                                json.dump(accounts, f, indent=4, ensure_ascii=False)
                            
                            # Replace original file with temporary file
                            if os.path.exists(temp_file):
                                if os.path.exists(self.accounts_file):
                                    os.remove(self.accounts_file)
                                os.rename(temp_file, self.accounts_file)
                            
                        except Exception as e:
                            print(f"Error saving to JSON file: {str(e)}")
                            # Try to restore from backup if available
                            if os.path.exists(f"{self.accounts_file}.bak"):
                                try:
                                    os.replace(f"{self.accounts_file}.bak", self.accounts_file)
                                    print("Restored from backup file")
                                except:
                                    pass
                            raise
                        
                        # Save to text file with proper encoding and error handling
                        try:
                            with open('accounts.txt', 'a', encoding='utf-8', errors='replace') as f:
                                f.write('\n' + '='*50 + '\n')
                                f.write(f"Account created at: {account_data['created_at']}\n")
                                f.write(f"Email: {account_data['email']}\n")
                                f.write(f"Password: {account_data['password']}\n")
                                f.write(f"STOVE ID: {account_data['stove_id']}\n")
                                f.write('='*50 + '\n')
                        except Exception as e:
                            print(f"Error saving to text file: {str(e)}")
                            # Continue even if text file save fails
                        
                        print("\nAccount successfully created and saved!")
                        print(f"Email: {account_data['email']}")
                        print(f"Password: {account_data['password']}")
                        print(f"STOVE ID: {account_data['stove_id']}")
                        
                        # Wait for 3 seconds then click Start STOVE button
                        time.sleep(3)
                        try:
                            # Try to find and click the Start STOVE button
                            start_button_selectors = [
                                "button.relative.w-full.stds-button.stds-button-primary",
                                "button.stds-button-primary",
                                "//button[contains(text(), 'Start STOVE')]",
                                "//button[contains(@class, 'stds-button-primary')]"
                            ]
                            
                            for selector in start_button_selectors:
                                try:
                                    if selector.startswith("//"):
                                        start_button = self.driver.find_element(By.XPATH, selector)
                                    else:
                                        start_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    if start_button:
                                        self.driver.execute_script("arguments[0].click();", start_button)
                                        print("Clicked Start STOVE button")
                                        break
                                except:
                                    continue
                        except:
                            print("Note: Could not find Start STOVE button")
                        
                        return True
                        
                    except Exception as e:
                        print(f"Error saving account: {str(e)}")
                        return False
                    
                except Exception as e:
                    print(f"Error processing completion: {str(e)}")
                    self.driver.save_screenshot("completion_error.png")
                    return False
                
            except Exception as e:
                print(f"Error reaching completion page: {str(e)}")
                self.driver.save_screenshot("completion_error.png")
                return False
            
        except Exception as e:
            print(f"Failed to create account: {str(e)}")
            import traceback
            traceback.print_exc()  # This will print the full error trace
            return False

    def _handle_captcha(self):
        """Handle CAPTCHA if present"""
        try:
            captcha_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "captcha"))
            )
            # Implement CAPTCHA handling logic here
            pass
        except TimeoutException:
            # No CAPTCHA found, continue
            pass
    
    def _save_account(self, credentials: Dict[str, str]):
        try:
            # Save to JSON file
            try:
                with open(self.accounts_file, 'r') as f:
                    accounts = json.load(f)
            except FileNotFoundError:
                accounts = []
            
            # Add new account with timestamp
            account_data = {
                **credentials,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            accounts.append(account_data)
            
            # Save updated accounts list to JSON
            with open(self.accounts_file, 'w') as f:
                json.dump(accounts, f, indent=4)
            
            # Save to accounts.txt in readable format
            with open('accounts.txt', 'a', encoding='utf-8') as f:
                f.write('\n' + '='*50 + '\n')
                f.write(f"Account created at: {account_data['created_at']}\n")
                f.write(f"Email: {credentials['email']}\n")
                f.write(f"Password: {credentials['password']}\n")
                if 'stove_id' in credentials:
                    f.write(f"STOVE ID: {credentials['stove_id']}\n")
                f.write('='*50 + '\n')
            
            print(f"\nAccount credentials saved to accounts.txt:")
            print(f"Email: {credentials['email']}")
            print(f"Password: {credentials['password']}")
            if 'stove_id' in credentials:
                print(f"STOVE ID: {credentials['stove_id']}")
                
        except Exception as e:
            print(f"Error saving account: {str(e)}")
    
    def close(self):
        """Clean up resources properly"""
        try:
            if hasattr(self, 'email_handler'):
                print("Closing email handler...")
                self.email_handler.close()
            
            if hasattr(self, 'driver'):
                print("Closing main driver...")
                try:
                    # Switch to main window if possible
                    if len(self.driver.window_handles) > 0:
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    self.driver.quit()
                except:
                    pass
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    def handle_verification(self, verification_code):
        """Helper method to handle verification code entry with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # ... (same code as above, but without the recursive retry) ...
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Verification attempt {attempt + 1} failed, retrying...")
                    self.human_delay(1, 2)
                else:
                    print("All verification attempts failed")
                    raise
        return False

    def find_member_info(self):
        """Helper method to find member info section"""
        member_info_selectors = [
            ".member-info",
            ".account-info",
            ".basic-information",
            "#userInfo",
            "//div[contains(@class, 'member')]",
            "//div[contains(@class, 'user-info')]"
        ]
        
        for selector in member_info_selectors:
            try:
                if selector.startswith("//"):
                    member_info = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    member_info = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                print(f"Found member info using selector: {selector}")
                return member_info
            except:
                continue
        return None

    def get_stove_id(self):
        """Helper method to get STOVE ID"""
        stove_id_selectors = [
            "span[class*='text-primary']",
            ".stove-id",
            "#userId",
            "//span[contains(@class, 'text-primary')]",
            "//div[contains(text(), 'S1')]"
        ]
        
        for selector in stove_id_selectors:
            try:
                if selector.startswith("//"):
                    stove_id = self.driver.find_element(By.XPATH, selector)
                else:
                    stove_id = self.driver.find_element(By.CSS_SELECTOR, selector)
                stove_id_text = stove_id.text.strip()
                print(f"Found STOVE ID: {stove_id_text}")
                return stove_id_text
            except:
                continue
        return None

    def save_account_details(self, credentials, stove_id):
        """Helper method to save account details"""
        account_data = {
            "email": credentials["email"],
            "password": credentials["password"],
            "stove_id": stove_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "verified": True
        }
        
        # Save to JSON file
        try:
            with open(self.accounts_file, 'r') as f:
                accounts = json.load(f)
        except FileNotFoundError:
            accounts = []
        
        accounts.append(account_data)
        
        with open(self.accounts_file, 'w') as f:
            json.dump(accounts, f, indent=4)
        
        # Save to accounts.txt in readable format
        with open('accounts.txt', 'a', encoding='utf-8') as f:
            f.write('\n' + '='*50 + '\n')
            f.write(f"Account created at: {account_data['created_at']}\n")
            f.write(f"Email: {account_data['email']}\n")
            f.write(f"Password: {account_data['password']}\n")
            f.write(f"STOVE ID: {account_data['stove_id']}\n")
            f.write(f"Status: Verified on member page\n")
            f.write('='*50 + '\n')
        
        print("\nAccount successfully created and verified!")
        print(f"Email: {account_data['email']}")
        print(f"Password: {account_data['password']}")
        print(f"STOVE ID: {account_data['stove_id']}")
        print("Account verified on member page")

def is_valid_email(email: str) -> bool:
    """Validate email format using regex."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def main():
    generator = CrossfireAccountGenerator()
    try:
        # Generate 1 account as a test
        success = generator.create_account()
        if success:
            print("Account created successfully!")
        else:
            print("Failed to create account")
    finally:
        generator.close()

if __name__ == "__main__":
    main() 