import requests
import time
from typing import Optional, Dict, List
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import random
import string
import json
import os
import sys

class TempMailHandler:
    def __init__(self, driver=None):
        self.base_url = "https://yopmail.com"
        self.api_url = "https://web2.temp-mail.org/mailbox"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.email_address = None
        self.mailbox_hash = None
        
        # Store window handles
        if driver:
            self.main_driver = driver
            # Store the Stove window handle
            self.stove_handle = self.main_driver.current_window_handle
            print("Creating new window for YOPmail...")
            # Open new window
            self.main_driver.execute_script("window.open('');")
            # Switch to the new window
            self.driver = self.main_driver
            self.email_handle = self.driver.window_handles[-1]
            self.driver.switch_to.window(self.email_handle)
        else:
            print("Setting up new Chrome driver for YOPmail")
            self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver for yopmail.com"""
        try:
            print("Setting up Chrome driver for YOPmail...")
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--start-maximized')
            
            chromedriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver.exe")
            if getattr(sys, 'frozen', False):
                chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
                
            self.driver = uc.Chrome(
                driver_executable_path=chromedriver_path,
                options=options,
                version_main=133,
                use_subprocess=True,
                suppress_welcome=True
            )
            print("YOPmail Chrome driver setup complete")
            
        except Exception as e:
            print(f"Error setting up YOPmail driver: {str(e)}")
            raise

    def switch_to_email(self):
        """Switch to email window"""
        if hasattr(self, 'email_handle'):
            self.driver.switch_to.window(self.email_handle)
            print("Switched to YOPmail window")

    def switch_to_stove(self):
        """Switch to Stove window"""
        if hasattr(self, 'stove_handle'):
            self.driver.switch_to.window(self.stove_handle)
            print("Switched to Stove window")

    def create_email(self, used_emails=None) -> str:
        """Create a new temporary email address using yopmail generator"""
        if used_emails is None:
            used_emails = set()
        
        try:
            # Make sure we're in the email window
            self.switch_to_email()
            
            print("Navigating to yopmail email generator...")
            self.driver.get("https://yopmail.com/en/email-generator")
            self.driver.implicitly_wait(10)
            self.human_delay(2, 3)

            while True:  # Keep trying until we get a unique email
                # Click New button
                try:
                    new_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.md.but"))
                    )
                    new_button.click()
                    print("Clicked New button")
                    self.human_delay(2, 3)
                except Exception as e:
                    print(f"Could not click New button: {str(e)}")

                # Try multiple selectors for the email element
                selectors = [
                    "span.genytxt",
                    "div.geny span",
                    "#geny",
                    ".nw span"
                ]

                email_element = None
                for selector in selectors:
                    try:
                        email_element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if email_element and email_element.is_displayed():
                            break
                    except:
                        continue

                if not email_element:
                    raise Exception("Could not find email element")

                # Get the generated email address
                email_username = email_element.text.strip()
                if not email_username:
                    try:
                        email_input = self.driver.find_element(By.ID, "geny")
                        email_username = email_input.get_attribute("value")
                    except:
                        pass

                # Create full email address
                self.email_address = f"{email_username}@yopmail.com"
                
                # Check if email is unique
                if self.email_address not in used_emails:
                    used_emails.add(self.email_address)
                    print(f"Created temporary email: {self.email_address}")
                    break
                else:
                    print(f"Email {self.email_address} already used, generating new one...")
                    continue

            # Click Copy to clipboard button
            try:
                copy_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.material-icons-outlined")
                for button in copy_buttons:
                    if button.is_displayed():
                        button.click()
                        print("Clicked copy button")
                        break
                self.human_delay(1, 2)
            except:
                print("Note: Could not click copy button, but continuing...")

            # Click Check Inbox button
            try:
                inbox_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.md")
                for button in inbox_buttons:
                    if "check" in button.text.lower() or "inbox" in button.text.lower():
                        button.click()
                        print("Clicked Check Inbox button")
                        break
                self.human_delay(2, 3)
            except:
                print("Warning: Could not click Check Inbox button automatically")
                input("Please click the Check Inbox button manually and press Enter to continue...")

            # Switch to the inbox frame
            try:
                inbox_frame = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ifinbox"))
                )
                self.driver.switch_to.frame(inbox_frame)
                self.driver.switch_to.default_content()
            except:
                print("Note: Inbox frame not immediately available (this is normal for new email)")
            
            # After getting email, switch back to Stove
            self.switch_to_stove()
            return self.email_address

        except Exception as e:
            print(f"Error creating temporary email: {str(e)}")
            self.driver.save_screenshot("email_error.png")
            print("Screenshot saved as email_error.png")
            # Make sure to switch back to Stove even if there's an error
            self.switch_to_stove()
            raise

    def wait_for_verification_code(self, timeout: int = 60, check_interval: int = 5) -> Optional[str]:
        """Wait for and extract verification code from email"""
        if not self.email_address:
            raise ValueError("No email address created yet")
            
        try:
            # Switch to email window for checking
            self.switch_to_email()
            print(f"Waiting for verification code email...")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Refresh inbox
                    refresh_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#refresh"))
                    )
                    refresh_button.click()
                    print("Refreshed inbox")
                    self.human_delay(1, 2)
                    
                    # Switch to inbox iframe
                    inbox_frame = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "ifinbox"))
                    )
                    self.driver.switch_to.frame(inbox_frame)
                    
                    # Look for STOVE email with multiple selectors
                    email_selectors = [
                        "div.m[onclick*='STOVE']",
                        "div.m:contains('STOVE')",
                        "div.m:contains('Verification')",
                        "//div[contains(@class, 'm') and contains(text(), 'STOVE')]",
                        "//div[contains(@class, 'm') and contains(text(), 'Verification')]"
                    ]
                    
                    email_found = False
                    for selector in email_selectors:
                        try:
                            if selector.startswith("//"):
                                emails = self.driver.find_elements(By.XPATH, selector)
                            else:
                                emails = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            if emails:
                                # Click the first matching email
                                emails[0].click()
                                email_found = True
                                print("Found and clicked STOVE email")
                                break
                        except:
                            continue
                    
                    if email_found:
                        self.driver.switch_to.default_content()
                        
                        # Switch to mail content iframe
                        mail_frame = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "ifmail"))
                        )
                        self.driver.switch_to.frame(mail_frame)
                        
                        # Try multiple selectors for email content
                        content_selectors = [
                            "div.mail",
                            "div.mailcontent",
                            "div.mailmsg",
                            "#mail",
                            "//div[contains(@class, 'mail')]"
                        ]
                        
                        for selector in content_selectors:
                            try:
                                if selector.startswith("//"):
                                    email_content = WebDriverWait(self.driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, selector))
                                    )
                                else:
                                    email_content = WebDriverWait(self.driver, 5).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                    )
                                
                                if email_content:
                                    content_text = email_content.text
                                    print("Email content found:", content_text[:100] + "...")  # Print first 100 chars
                                    
                                    # Look for verification code with multiple patterns
                                    import re
                                    patterns = [
                                        r'\b\d{6}\b',  # 6 digits
                                        r'verification.*?(\d{6})',  # "verification" followed by 6 digits
                                        r'code.*?(\d{6})',  # "code" followed by 6 digits
                                        r'number.*?(\d{6})'  # "number" followed by 6 digits
                                    ]
                                    
                                    for pattern in patterns:
                                        codes = re.findall(pattern, content_text, re.IGNORECASE)
                                        if codes:
                                            verification_code = codes[0]
                                            print(f"Found verification code: {verification_code}")
                                            self.switch_to_stove()
                                            return verification_code
                                    
                                    break  # Exit content selector loop if content was found
                            except:
                                continue
                    
                    self.driver.switch_to.default_content()
                    print(f"No verification code yet, waiting {check_interval} seconds...")
                    time.sleep(check_interval)
                    
                except Exception as e:
                    print(f"Error checking email: {str(e)}")
                    self.driver.switch_to.default_content()
                    time.sleep(check_interval)
                
            print("Timeout waiting for verification code")
            self.switch_to_stove()
            return None
            
        except Exception as e:
            print(f"Error checking verification code: {str(e)}")
            self.switch_to_stove()
            return None

    def close(self):
        """Close only the email window if using shared driver"""
        if hasattr(self, 'main_driver'):
            # Switch to email window to close it
            self.switch_to_email()
            self.driver.close()
            # Switch back to Stove window
            self.switch_to_stove()
        elif hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def human_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add random delay to simulate human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds)) 