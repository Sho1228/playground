import requests
import json
import csv
import time
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging
import re
from concurrent.futures import ThreadPoolExecutor

class ColorPrint:
    """Color printing class for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def print_info(message):
        print(f"{ColorPrint.OKGREEN}ℹ️  {message}{ColorPrint.ENDC}")

    @staticmethod
    def print_success(message):
        print(f"{ColorPrint.OKGREEN}✅ {message}{ColorPrint.ENDC}")

    @staticmethod
    def print_warning(message):
        print(f"{ColorPrint.WARNING}⚠️  {message}{ColorPrint.ENDC}")

    @staticmethod
    def print_error(message):
        print(f"{ColorPrint.FAIL}❌ {message}{ColorPrint.ENDC}")

    @staticmethod
    def print_header(message):
        print(f"{ColorPrint.HEADER}{ColorPrint.BOLD}🔍 {message}{ColorPrint.ENDC}")

    @staticmethod
    def print_data(label, value):
        print(f"{ColorPrint.OKCYAN}📊 {label}: {ColorPrint.OKBLUE}{value}{ColorPrint.ENDC}")

    @staticmethod
    def print_status(message):
        print(f"{ColorPrint.OKBLUE}🔄 {message}{ColorPrint.ENDC}")

class FixedInstagramLogger:
    def __init__(self):
        # Updated to track "heyheyhey" specifically
        self.target_username = "heyhowareyour"  # Instagram username
        self.target_display_name = "heyheyhey"  # Display name to search for in DMs
        self.target_url = "https://www.instagram.com/heyhowareyour/"
        self.monitoring_interval = 5
        self.driver = None
        
        # CSV file paths
        self.profile_csv = 'user_profile.csv'
        self.activity_csv = 'activity_monitor.csv'
        
        self.setup_logging()
        self.setup_csv_files()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        ColorPrint.print_header(f"Instagram Logger - Tracking Display Name: '{self.target_display_name}' 🎯")
        
    def setup_csv_files(self):
        """Initialize CSV files"""
        ColorPrint.print_status("Setting up CSV files...")
        
        if not os.path.exists(self.profile_csv):
            with open(self.profile_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'username', 'full_name', 'bio', 'follower_count', 
                    'following_count', 'post_count', 'profile_pic_url', 
                    'is_private', 'is_verified', 'last_updated'
                ])
        
        if not os.path.exists(self.activity_csv):
            with open(self.activity_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'username', 'check_timestamp', 'online_status', 'last_seen',
                    'profile_accessible', 'response_time_ms', 'error_message'
                ])
                
        ColorPrint.print_success("CSV files ready")
        
    def initialize_browser(self, headless=True):
        """Initialize browser"""
        try:
            ColorPrint.print_status("Initializing browser...")
            
            options = Options()
            if headless:
                options.add_argument('--headless')
                
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--window-size=1280,720')
            
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.driver.implicitly_wait(5)
            self.driver.set_page_load_timeout(20)
            
            ColorPrint.print_success("Browser ready")
            return True
            
        except Exception as e:
            ColorPrint.print_error(f"Browser init failed: {str(e)}")
            return False
            
    def load_cookies_only(self, cookie_file='instagram_cookies.json'):
        """Load cookies without verification"""
        if not os.path.exists(cookie_file):
            ColorPrint.print_error(f"Cookie file {cookie_file} not found")
            return False
            
        try:
            ColorPrint.print_status("Loading cookies...")
            
            self.driver.get('https://www.instagram.com/')
            time.sleep(3)
            
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
                
            for cookie in cookies:
                try:
                    if 'name' in cookie and 'value' in cookie:
                        self.driver.add_cookie({
                            'name': cookie['name'],
                            'value': cookie['value'],
                            'domain': cookie.get('domain', '.instagram.com'),
                            'path': cookie.get('path', '/'),
                        })
                except:
                    continue
                    
            ColorPrint.print_success("Cookies loaded")
            return True
                
        except Exception as e:
            ColorPrint.print_error(f"Cookie loading failed: {str(e)}")
            return False

    def extract_profile_data_robust(self):
        """Extract profile data for the target username"""
        try:
            start_time = time.time()
            ColorPrint.print_status(f"Extracting profile data for @{self.target_username}...")
            
            # Navigate to profile
            self.driver.get(self.target_url)
            time.sleep(5)
            
            profile_data = {
                'username': self.target_username,
                'profile_accessible': True,
                'error_message': None
            }
            
            page_source = self.driver.page_source
            
            # Save page source for debugging
            with open('profile_debug.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            ColorPrint.print_info("Page source saved to profile_debug.html")
            
            # Extract using visible element selectors
            try:
                # Full name
                full_name = None
                name_selectors = [
                    "header section h2",
                    "h2[dir='auto']", 
                    "header h1",
                    "span[dir='auto']",
                    "header section div h2"
                ]
                
                for selector in name_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            text = elem.text.strip()
                            if text and len(text) > 0 and len(text) < 100:
                                full_name = text
                                ColorPrint.print_success(f"Found full name: {full_name}")
                                break
                        if full_name:
                            break
                    except:
                        continue
                
                profile_data['full_name'] = full_name
                
                # Stats extraction
                try:
                    stat_elements = self.driver.find_elements(By.XPATH, "//header//a | //header//span")
                    
                    numbers_found = []
                    for elem in stat_elements:
                        try:
                            text = elem.text.strip()
                            href = elem.get_attribute('href') or ''
                            
                            if re.search(r'\d+[KMkm]?', text):
                                number = self.extract_number_from_text(text)
                                if number is not None:
                                    numbers_found.append((number, text, href))
                                    ColorPrint.print_info(f"Found number: {number:,} from text: '{text}'")
                        except:
                            continue
                    
                    # Identify numbers by href
                    for number, text, href in numbers_found:
                        if 'followers' in href:
                            profile_data['follower_count'] = number
                            ColorPrint.print_success(f"Followers: {number:,}")
                        elif 'following' in href:
                            profile_data['following_count'] = number
                            ColorPrint.print_success(f"Following: {number:,}")
                    
                    # Position-based assignment if href detection fails
                    if len(numbers_found) >= 3 and 'follower_count' not in profile_data:
                        profile_data['post_count'] = numbers_found[0][0]
                        profile_data['follower_count'] = numbers_found[1][0]
                        profile_data['following_count'] = numbers_found[2][0]
                        ColorPrint.print_success(f"Position-based assignment:")
                        ColorPrint.print_data("Posts", f"{numbers_found[0][0]:,}")
                        ColorPrint.print_data("Followers", f"{numbers_found[1][0]:,}")
                        ColorPrint.print_data("Following", f"{numbers_found[2][0]:,}")
                
                except Exception as e:
                    ColorPrint.print_warning(f"Stats extraction failed: {str(e)}")
                
                # Profile picture URL
                try:
                    profile_pic_selectors = [
                        "header img",
                        "img[alt*='profile picture']",
                        "img[alt*='Profile picture']",
                        "header div img"
                    ]
                    
                    for selector in profile_pic_selectors:
                        try:
                            img_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if img_elem:
                                src = img_elem.get_attribute('src')
                                if src and 'instagram' in src:
                                    profile_data['profile_pic_url'] = src
                                    ColorPrint.print_success("Found profile picture URL")
                                    break
                        except:
                            continue
                
                except Exception as e:
                    ColorPrint.print_warning(f"Profile pic extraction failed: {str(e)}")
                
                # Bio extraction
                try:
                    bio_selectors = [
                        "header section div span",
                        "span[dir='auto']",
                        "header div span"
                    ]
                    
                    for selector in bio_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                text = elem.text.strip()
                                if text and len(text) > 10 and len(text) < 500 and text != full_name:
                                    profile_data['bio'] = text
                                    ColorPrint.print_success(f"Found bio: {text[:50]}...")
                                    break
                            if profile_data.get('bio'):
                                break
                        except:
                            continue
                
                except Exception as e:
                    ColorPrint.print_warning(f"Bio extraction failed: {str(e)}")
                
            except Exception as e:
                ColorPrint.print_error(f"Element-based extraction failed: {str(e)}")
            
            # Check private/verified status
            profile_data['is_private'] = 'This account is private' in page_source
            profile_data['is_verified'] = 'is_verified":true' in page_source or 'Verified' in page_source
            
            elapsed = int((time.time() - start_time) * 1000)
            profile_data['response_time_ms'] = elapsed
            
            return profile_data
            
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            ColorPrint.print_error(f"Profile extraction failed ({elapsed}ms): {str(e)}")
            return None

    def extract_number_from_text(self, text):
        """Extract number from text handling K, M suffixes"""
        try:
            text = text.replace(',', '').strip()
            
            match = re.search(r'([\d\.]+)\s*([KMkm]?)', text)
            if match:
                number_str, suffix = match.groups()
                number = float(number_str)
                
                if suffix.lower() == 'k':
                    number *= 1000
                elif suffix.lower() == 'm':
                    number *= 1000000
                
                return int(number)
            
            number_match = re.search(r'\d+', text)
            if number_match:
                return int(number_match.group())
                
        except:
            pass
        
        return None

    def search_for_specific_user_activity(self):
        """Search specifically for 'heyheyhey' display name in DM interface"""
        try:
            start_time = time.time()
            ColorPrint.print_status(f"Searching specifically for display name: '{self.target_display_name}'...")
            
            # Navigate to DM
            self.driver.get("https://www.instagram.com/direct/inbox/")
            time.sleep(5)
            
            # Save DM page for debugging
            with open('dm_debug.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            ColorPrint.print_info("DM page source saved to dm_debug.html")
            
            # Method 1: Look for existing conversations with the display name
            ColorPrint.print_status("Method 1: Searching existing conversations...")
            
            # Look for elements containing the display name
            display_name_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{self.target_display_name}')]")
            
            if display_name_elements:
                ColorPrint.print_success(f"Found '{self.target_display_name}' in conversation list!")
                
                # Click on the conversation with this display name
                for elem in display_name_elements:
                    try:
                        # Check if this element is clickable (conversation item)
                        parent = elem.find_element(By.XPATH, "./ancestor::*[@role='button' or @role='link' or contains(@class, 'conversation') or contains(@class, 'chat')]")
                        if parent:
                            parent.click()
                            time.sleep(3)
                            ColorPrint.print_success(f"Clicked on conversation with '{self.target_display_name}'")
                            break
                    except:
                        # Try clicking the element itself
                        try:
                            elem.click()
                            time.sleep(3)
                            ColorPrint.print_success(f"Clicked on '{self.target_display_name}' element")
                            break
                        except:
                            continue
                
                # Now look for activity status in this specific conversation
                return self.parse_activity_status_from_conversation()
            
            # Method 2: Use search functionality to find the user
            ColorPrint.print_status("Method 2: Using search to find user...")
            
            # Look for search input
            search_selectors = [
                "input[placeholder*='検索']",     # Japanese
                "input[placeholder*='Search']",   # English
                "input[type='text']",
                "[data-testid='search-input']"
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        if inp.is_displayed() and inp.is_enabled():
                            search_input = inp
                            break
                    if search_input:
                        break
                except:
                    continue
            
            if search_input:
                ColorPrint.print_success("Found search input, searching for display name...")
                
                # Search for the display name
                search_input.clear()
                search_input.send_keys(self.target_display_name)
                time.sleep(3)
                
                # Look for search results with the display name
                search_results = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{self.target_display_name}')]")
                
                if search_results:
                    ColorPrint.print_success(f"Found '{self.target_display_name}' in search results!")
                    
                    # Click on the search result
                    search_results[0].click()
                    time.sleep(3)
                    
                    # Parse activity status
                    return self.parse_activity_status_from_conversation()
                else:
                    ColorPrint.print_warning(f"Display name '{self.target_display_name}' not found in search results")
            else:
                ColorPrint.print_warning("Search input not found")
            
            # Method 3: Try alternative search with username
            ColorPrint.print_status("Method 3: Searching with username as fallback...")
            
            if search_input:
                search_input.clear()
                search_input.send_keys(self.target_username)
                time.sleep(3)
                
                username_results = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{self.target_username}')]")
                if username_results:
                    ColorPrint.print_success(f"Found '{self.target_username}' in search results!")
                    username_results[0].click()
                    time.sleep(3)
                    return self.parse_activity_status_from_conversation()
            
            elapsed = int((time.time() - start_time) * 1000)
            ColorPrint.print_warning(f"Could not find '{self.target_display_name}' using any method ({elapsed}ms)")
            return "unknown", None
            
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            ColorPrint.print_error(f"User search failed ({elapsed}ms): {str(e)}")
            return "unknown", None

    def parse_activity_status_from_conversation(self):
        """Parse activity status from the opened conversation"""
        try:
            ColorPrint.print_status("Parsing activity status from conversation...")
            
            page_source = self.driver.page_source
            
            # Save conversation page for debugging
            with open('conversation_debug.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            ColorPrint.print_info("Conversation page saved to conversation_debug.html")
            
            # Japanese activity patterns
            japanese_activity = re.search(r'(\d+)(分前|時間前|日前|週間).*?オンライン', page_source)
            if japanese_activity:
                time_value, time_unit = japanese_activity.groups()
                
                if time_unit == '分前':
                    status, last_seen = "recently_active", f"{time_value}分前にオンライン"
                elif time_unit == '時間前':
                    status, last_seen = "recently_active", f"{time_value}時間前にオンライン"
                elif time_unit == '日前':
                    status, last_seen = "offline", f"{time_value}日前にオンライン"
                else:
                    status, last_seen = "offline", f"{time_value}週間前"
                    
                ColorPrint.print_success(f"🎯 Found activity for '{self.target_display_name}': {last_seen}")
                return status, last_seen
            
            # English activity patterns
            english_activity = re.search(r'Active (\d+)(m|h|d) ago', page_source, re.IGNORECASE)
            if english_activity:
                time_value, time_unit = english_activity.groups()
                
                if time_unit == 'm':
                    status, last_seen = "recently_active", f"Active {time_value}m ago"
                elif time_unit == 'h':
                    status, last_seen = "recently_active", f"Active {time_value}h ago"
                else:
                    status, last_seen = "offline", f"Active {time_value}d ago"
                    
                ColorPrint.print_success(f"🎯 Found activity for '{self.target_display_name}': {last_seen}")
                return status, last_seen
            
            # Online now check
            if re.search(r'(Active now|オンライン中)', page_source, re.IGNORECASE):
                ColorPrint.print_success(f"🎯 '{self.target_display_name}' is online now!")
                return "online", "Active now"
            
            ColorPrint.print_warning(f"No activity status found for '{self.target_display_name}'")
            return "unknown", None
            
        except Exception as e:
            ColorPrint.print_error(f"Activity parsing failed: {str(e)}")
            return "unknown", None

    def save_to_csv(self, profile_data, activity_data):
        """Save data to CSV"""
        try:
            # Save profile data
            with open(self.profile_csv, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    profile_data.get('username', ''),
                    profile_data.get('full_name', ''),
                    profile_data.get('bio', ''),
                    profile_data.get('follower_count', ''),
                    profile_data.get('following_count', ''),
                    profile_data.get('post_count', ''),
                    profile_data.get('profile_pic_url', ''),
                    profile_data.get('is_private', False),
                    profile_data.get('is_verified', False),
                    datetime.now().isoformat()
                ])
            
            # Save activity data
            with open(self.activity_csv, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    self.target_username,
                    datetime.now().isoformat(),
                    activity_data[0],
                    activity_data[1],
                    profile_data.get('profile_accessible', False),
                    profile_data.get('response_time_ms', 0),
                    profile_data.get('error_message', '')
                ])
                
            ColorPrint.print_success("Data saved to CSV")
            
        except Exception as e:
            ColorPrint.print_error(f"CSV save failed: {str(e)}")

    def export_cookies_for_first_setup(self):
        """Cookie setup"""
        ColorPrint.print_header("FIRST TIME SETUP")
        ColorPrint.print_info("1. Chrome will open - log into Instagram manually")
        ColorPrint.print_info("2. Press Enter when logged in")
        
        try:
            options = Options()
            options.add_argument('--window-size=1400,1000')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get('https://www.instagram.com/')
            input(f"\n{ColorPrint.OKCYAN}Press Enter after logging into Instagram...{ColorPrint.ENDC}")
            
            cookies = driver.get_cookies()
            with open('instagram_cookies.json', 'w') as f:
                json.dump(cookies, f, indent=2)
                
            ColorPrint.print_success("Cookies saved!")
            
        except Exception as e:
            ColorPrint.print_error(f"Setup failed: {str(e)}")
        finally:
            if 'driver' in locals():
                driver.quit()

    def start_monitoring(self, headless=True):
        """Start monitoring with specific user tracking"""
        ColorPrint.print_header(f"🎯 Instagram Monitor - Tracking '{self.target_display_name}'")
        ColorPrint.print_data("Username", f"@{self.target_username}")
        ColorPrint.print_data("Display Name", f"'{self.target_display_name}'")
        ColorPrint.print_warning("Will specifically search for this display name, not most recent chat")
        
        if not self.initialize_browser(headless=headless):
            return
            
        if not self.load_cookies_only():
            ColorPrint.print_error("Cookie loading failed. Run setup first.")
            self.driver.quit()
            return
            
        check_count = 0
        
        try:
            while True:
                check_count += 1
                cycle_start = time.time()
                
                ColorPrint.print_header(f"🎯 Specific Check #{check_count} for '{self.target_display_name}'")
                
                profile_data = self.extract_profile_data_robust()
                activity_data = self.search_for_specific_user_activity()
                
                if profile_data:
                    self.save_to_csv(profile_data, activity_data)
                    
                    cycle_time = int((time.time() - cycle_start) * 1000)
                    ColorPrint.print_success(f"🎯 Complete cycle: {cycle_time}ms")
                    
                    if activity_data[0] != "unknown":
                        ColorPrint.print_data("Activity Status", f"{activity_data[0]}: {activity_data[1]}")
                else:
                    ColorPrint.print_error("Check failed")
                    
                ColorPrint.print_status(f"Next check in {self.monitoring_interval} minutes...")
                time.sleep(self.monitoring_interval * 60)
                
        except KeyboardInterrupt:
            ColorPrint.print_warning("Monitoring stopped")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    logger = FixedInstagramLogger()
    
    if not os.path.exists('instagram_cookies.json'):
        ColorPrint.print_warning("No cookies found. Running setup...")
        logger.export_cookies_for_first_setup()
        return
    
    ColorPrint.print_header("🎯 Instagram Monitor - Specific User Tracking")
    ColorPrint.print_info(f"Will track display name: '{logger.target_display_name}' specifically")
    ColorPrint.print_warning("Not tracking most recent chat - searching for specific user")
    
    run_mode = input(f"{ColorPrint.OKCYAN}Visual (v) or Background (b)? [v/b]: {ColorPrint.ENDC}").strip().lower()
    headless_mode = run_mode in ['b', 'background']
    
    logger.start_monitoring(headless=headless_mode)

if __name__ == "__main__":
    main()
