import time
import json
import urllib.parse 
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GradCafeScraper:
    # Based on the HTML you provided, the canonical link uses /survey/index.php
    BASE_URL = "https://www.thegradcafe.com/survey/index.php"
    
    def __init__(self, output_file="raw_applicant_data.json"):
        self.output_file = output_file
        self.raw_data = []
        self.driver = None
        
        # --- 1. AUTO-RESUME LOGIC ---
        # Try to load existing data to prevent starting over
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            print(f"Loaded {len(self.raw_data)} existing entries. Resuming scrape...")
        except FileNotFoundError:
            print("No existing file found. Starting fresh.")
            self.raw_data = []
        except ValueError: # Handle corrupt JSON
            self.raw_data = []

    def _setup_driver(self):
        """Helper to create/recreate the driver"""
        # If driver exists, try to close it cleanly first
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
                
        options = Options()
        # options.add_argument("--headless") # Keep commented to monitor progress
        options.add_argument("--disable-blink-features=AutomationControlled") 
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Memory saving flags to prevent "Max retries exceeded"
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver

    def scrape_data(self, target_count=30001):
        if not self.driver:
            self.driver = self._setup_driver()
            
        # --- 2. CALCULATE START PAGE ---
        # Your HTML shows about 25 entries per page.
        # We calculate which page to jump to based on how much data we already have.
        if len(self.raw_data) > 0:
            # Integer division to find page
            current_page = (len(self.raw_data) // 25) 
            if current_page < 1: current_page = 1
        else:
            current_page = 1
            
        print(f"--- STARTING SCRAPE AT PAGE {current_page} ---")
        
        try:
            while len(self.raw_data) < target_count:
                # --- 3. ROBUST NAVIGATION ---
                # Based on the HTML: <a href="/survey/?page=2">
                # We construct the URL manually to "Jump" to the specific page.
                # This fixes the issue of not being able to click "Next" if the page didn't load perfectly.
                params = {'q': '*', 'page': current_page} 
                target_url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
                
                # Retry Loop for Page Load (Handles your "Max retries" and "Timeout" errors)
                success = False
                attempts = 0
                while not success and attempts < 3:
                    try:
                        self.driver.get(target_url)
                        
                        # Wait for the table rows (tr) to ensure data is present
                        WebDriverWait(self.driver, 20).until(
                            EC.presence_of_element_located((By.TAG_NAME, "tr"))
                        )
                        success = True
                    except Exception as e:
                        attempts += 1
                        print(f"Error loading page {current_page} (Attempt {attempts}): {e}")
                        
                        # If we timed out or crashed, RESTART THE DRIVER
                        print("♻️ Restarting Browser Driver to clear memory...")
                        self.driver = self._setup_driver()
                        time.sleep(5) # Give it a moment to settle
                
                if not success:
                    print(f"Skipping page {current_page} due to persistent errors.")
                    current_page += 1
                    continue

                # --- 4. DATA EXTRACTION ---
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Check for Cloudflare Block
                if "Just a moment" in soup.get_text():
                    print("⚠️ Cloudflare detected. Pausing 45 seconds...")
                    time.sleep(45)
                    # Don't increment page, try this one again
                    continue

                new_entries = self._extract_data_from_soup(soup, target_url)
                
                if not new_entries:
                    print(f"No entries found on page {current_page}. (Might be end of results).")
                    # We check if we are at page 1 (blocked) or deep (end of data)
                    if current_page == 1:
                        break
                    # If deep, maybe just a glitchy page, try next
                    current_page += 1
                    continue

                self.raw_data.extend(new_entries)
                print(f"Pg {current_page} | Collected: {len(new_entries)} | Total: {len(self.raw_data)}")
                
                current_page += 1
                
                # --- 5. SAFETY SAVE & CLEANUP ---
                # Save every 5 pages so you don't lose 23k entries again
                if current_page % 5 == 0:
                    self.save_raw_data()
                    
                # Restart driver every 50 pages to free up RAM (Prevents HTTPConnectionPool error)
                if current_page % 50 == 0:
                    print("♻️ Periodic Driver Restart (Maintenance)...")
                    self.driver = self._setup_driver()
                
                time.sleep(2) # Politeness delay

        except KeyboardInterrupt:
            print("Scraping stopped by user.")
        except Exception as e:
            print(f"Critical Error: {e}")
        finally:
            self._teardown()
            
        return self.raw_data[:target_count]

    def _extract_data_from_soup(self, soup, url):
        """
        Extracts data using the structure from the HTML provided.
        """
        entries = []
        rows = soup.find_all('tr')
        
        current_entry = None

        for row in rows:
            cells = row.find_all('td')
            
            # --- Identify Main Row ---
            # Based on your HTML, the main row has the University name in a div with font-medium
            is_main_row = False
            if len(cells) >= 2:
                if row.find('div', class_=lambda x: x and 'font-medium' in x):
                    is_main_row = True

            if is_main_row:
                if current_entry:
                    entries.append(current_entry)

                # Extract University
                school = cells[0].get_text(strip=True)
                
                # Extract Program & Degree (Col 2)
                # Structure: <div><span>Program</span> <svg> <span>Degree</span></div>
                prog_block = cells[1]
                spans = prog_block.find_all('span')
                
                prog_text = spans[0].get_text(strip=True) if len(spans) > 0 else ""
                degree_text = spans[-1].get_text(strip=True) if len(spans) > 1 else "Other"

                # Extract Full Row Text for regex processing later (Status, Date, etc)
                # This ensures we capture "Accepted on 30 Jan" even if classes change
                full_row_text = row.get_text(" ", strip=True)
                
                current_entry = {
                    "raw_inst": school,
                    "raw_prog": prog_text,
                    "raw_degree": degree_text,
                    "raw_text": full_row_text, 
                    "raw_comments": "",
                    "url": url
                }
            
            elif current_entry:
                # --- Identify Detail Rows ---
                # Row with Stats badges (GPA, GRE, Season)
                # Row with Comments (<p> tags)
                
                # Comments often in a <p> tag in a cell spanning multiple columns
                comment_p = row.find('p')
                if comment_p:
                    current_entry["raw_comments"] += " " + comment_p.get_text(strip=True)
                
                # Stats are usually in the raw text of these detail rows too
                current_entry["raw_text"] += " " + row.get_text(" ", strip=True)

        if current_entry:
            entries.append(current_entry)
            
        return entries

    def save_raw_data(self):
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.raw_data, f, indent=4)
            print(f"Saved {len(self.raw_data)} entries.")
        except Exception as e:
            print(f"Error saving: {e}")

    def _teardown(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    scraper = GradCafeScraper()
    scraper.scrape_data(target_count=30001)
    scraper.save_raw_data()