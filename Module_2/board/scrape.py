import re
import time
import json
import urllib.parse 
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class GradCafeScraper:
    BASE_URL = "https://www.thegradcafe.com/survey/index.php"
    
    def __init__(self, output_file="raw_applicant_data.json"):
        self.output_file = output_file
        self.raw_data = []
        self.driver = self._setup_driver()

    def _setup_driver(self):
        options = Options()
        # options.add_argument("--headless") # Uncomment to run in background
        options.add_argument("--disable-blink-features=AutomationControlled") 
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver

    def scrape_data(self, target_count=50):
        print("--- STARTED ---")
        
        # Initial URL
        params = {'q': '*', 't': 'a', 'o': '', 'p': 1}
        current_url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        
        try:
            while len(self.raw_data) < target_count:
                print(f"Navigating to: {current_url}")
                self.driver.get(current_url)
                
                # Wait for table rows to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "tr"))
                    )
                except:
                    print("Timeout waiting for rows.")

                time.sleep(3) # Fixed delay instead of random
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Extract data
                new_entries = self._extract_data_from_soup(soup, current_url)
                
                if not new_entries:
                    print("No entries found on this page. Stopping.")
                    break
                
                self.raw_data.extend(new_entries)
                print(f"Collected {len(self.raw_data)} total entries.")
                
                if len(self.raw_data) >= target_count:
                    break

                # Pagination Logic
                try:
                    # Find the 'Next' button specifically using the text inside the pagination nav
                    next_button = self.driver.find_element(By.XPATH, "//a[contains(., 'Next')]")
                    next_url = next_button.get_attribute("href")
                    
                    if next_url and next_url != current_url:
                        current_url = next_url
                    else:
                        break
                except NoSuchElementException:
                    print("No 'Next' button found. Finished.")
                    break

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self._teardown()
        return self.raw_data[:target_count]

    def _extract_data_from_soup(self, soup, url):
        """
        Parses the HTML table handling multi-row entries.
        Row 1: Main Info (School, Prog, Decision)
        Row 2 (Optional): Badges (GPA, GRE, Season, Status)
        Row 3 (Optional): Comments (Text)
        """
        entries = []
        rows = soup.find_all('tr')
        
        current_entry = None

        for row in rows:
            # Check if this is a "Main Data" row (it has the School column)
            cells = row.find_all('td')
            
            is_main_row = False
            if len(cells) >= 2:
                # Check for School Name container
                if row.find('div', class_='tw-font-medium tw-text-gray-900 tw-text-sm'):
                    is_main_row = True

            if is_main_row:
                # If we were building an entry, save it before starting a new one
                if current_entry:
                    entries.append(current_entry)

                # --- Extract Main Row Data ---
                school_cell = cells[0].get_text(strip=True)
                program_degree_cell = cells[1]
                
                # Split Program and Degree
                prog_text = ""
                degree_text = "Other" 
                
                spans = program_degree_cell.find_all('span')
                if len(spans) >= 1:
                    prog_text = spans[0].get_text(strip=True)
                if len(spans) >= 2:
                    degree_text = spans[-1].get_text(strip=True)

                decision_cell_text = ""
                date_added = ""
                
                # Loop to find the decision badge specifically
                for cell in cells:
                    badge = cell.find('div', class_=lambda x: x and 'ring-inset' in x)
                    if badge:
                        decision_cell_text = badge.get_text(strip=True)
                    elif "202" in cell.get_text(): 
                         date_added = cell.get_text(strip=True)

                # Parse Status
                status = "Other"
                if "Accepted" in decision_cell_text:
                    status = "Accepted"
                elif "Rejected" in decision_cell_text:
                    status = "Rejected"
                elif "Wait listed" in decision_cell_text:
                    status = "Waitlisted"
                elif "Interview" in decision_cell_text:
                    status = "Interview"
                
                # Initialize Object
                current_entry = {
                    "University": school_cell,
                    "Program Name": prog_text,
                    "Masters or PhD": degree_text,
                    "Applicant Status": status,
                    "Date of Information Added": date_added,
                    "Decision Details": decision_cell_text,
                    "Season": None,
                    "International / American Student": None,
                    "GPA": None,
                    "GRE Score": None,
                    "GRE V Score": None,
                    "GRE AW": None,
                    "Comments": None,
                    "URL link": url
                }

            # If it's NOT a main row, it might be stats or comments
            elif current_entry:
                # Check for Comments
                comment_p = row.find('p')
                if comment_p:
                    current_entry["Comments"] = comment_p.get_text(strip=True)
                    continue 

                # Check for Stats (Badges)
                badges = row.find_all('div', class_=lambda x: x and ('rounded-md' in x or 'ring-inset' in x))
                
                for badge in badges:
                    txt = badge.get_text(strip=True)
                    
                    if re.search(r'(Fall|Spring|Summer)\s*20\d{2}', txt):
                        current_entry["Season"] = txt
                    
                    elif txt in ["International", "American"]:
                        current_entry["International / American Student"] = txt
                        
                    elif "GPA" in txt:
                        match = re.search(r'GPA\s*([\d\.]+)', txt)
                        if match:
                            current_entry["GPA"] = match.group(1)
                            
                    elif "GRE" in txt and "V" not in txt and "AW" not in txt:
                        match = re.search(r'GRE\s*(\d+)', txt)
                        if match:
                            current_entry["GRE Score"] = match.group(1)

                    elif "GRE V" in txt:
                        match = re.search(r'GRE V\s*(\d+)', txt)
                        if match:
                            current_entry["GRE V Score"] = match.group(1)

                    elif "GRE AW" in txt:
                        match = re.search(r'GRE AW\s*([\d\.]+)', txt)
                        if match:
                            current_entry["GRE AW"] = match.group(1)

        # Append the very last entry
        if current_entry:
            entries.append(current_entry)
            
        return entries

    def save_raw_data(self):
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.raw_data, f, indent=4)
        print(f"Data saved to {self.output_file}")

    def _teardown(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    scraper = GradCafeScraper()
    scraper.scrape_data(target_count=10)
    scraper.save_raw_data()