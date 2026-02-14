import json
import re
import urllib3
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# Import the DataCleaner class from your clean.py file
# This allows us to "push" the data to the cleaner immediately after scraping
try:
    from clean import DataCleaner
except ImportError:
    try:
        from board.clean import DataCleaner
    except ImportError:
        print("Warning: clean.py not found. Data will be scraped but not cleaned/merged.")
        DataCleaner = None

class GradCafeScraper:
    BASE_URL = "https://www.thegradcafe.com/survey/index.php"

    def __init__(self, output_file="raw_applicant_data.json", debug=True):
        base_dir = __file__.rsplit("\\", 1)[0]
        if output_file and not (output_file.startswith("\\") or ":" in output_file):
            output_file = base_dir + "\\" + output_file
        self.output_file = output_file
        self.debug = debug
        self.raw_data = []
        self.http = self._setup_http()
        self.latest_stored_date = None

        # AUTO-RESUME LOGIC 
        try:
            with open(self.output_file, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)
            
            if not isinstance(self.raw_data, list):
                print("JSON root is not a list. Starting fresh.")
                self.raw_data = []
            
            # Identify the most recent date in the existing file to know when to stop
            if len(self.raw_data) > 0:
                for entry in self.raw_data:
                    if entry.get("raw_date"):
                        self.latest_stored_date = entry.get("raw_date")
                        print(f"Loaded existing raw data. Will stop scraping if date matches: {self.latest_stored_date}")
                        break
        except FileNotFoundError:
            print("No existing raw file found. Starting fresh.")
            self.raw_data = []
        except Exception:
            print("Existing JSON is corrupt or invalid. Starting fresh.")
            self.raw_data = []

    def _setup_http(self):
        retry = Retry(
            total=10,
            connect=5,
            read=5,
            redirect=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )

        return urllib3.PoolManager(
            retries=retry,
            timeout=urllib3.Timeout(connect=10.0, read=30.0),
            cert_reqs="CERT_REQUIRED",
        )

    def _build_url(self, page: int) -> str:
        return f"{self.BASE_URL}?q=%2A&t=a&o=&page={page}"

    def _fetch_html(self, url: str) -> str | None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
            "Referer": "https://www.thegradcafe.com/",
        }

        try:
            r = self.http.request("GET", url, headers=headers, preload_content=False)
            raw = r.read(decode_content=True)
            text = raw.decode("utf-8", errors="replace")

            if self.debug:
                ctype = r.headers.get("content-type")
                print(f"[DEBUG] HTTP {r.status} | CT={ctype} | {url}")

            if r.status >= 400 and r.status != 429:
                print(f"HTTP {r.status} for {url}")
                return None

            return text
        except Exception as e:
            print(f"Request failed for {url}: {e}")
            return None

    def scrape_data(self, target_count=50000, save_every_pages=8, max_empty_pages=10, max_pages=None):
        # Always start at Page 1 to get the newest updates
        current_page = 1
        pages_scraped_session = 0
        if max_pages is None:
            # Determine max pages based on whether applicant_data.json exists
            try:
                base_dir = __file__.rsplit("\\", 1)[0]
                applicant_path = base_dir + "\\..\\applicant_data.json"
                with open(applicant_path, "r", encoding="utf-8"):
                    max_pages = 5
                    print("Existing 'applicant_data.json' found. Limiting scrape to 5 pages.")
            except FileNotFoundError:
                max_pages = 10000
            except Exception:
                max_pages = 10000
        print(f"--- STARTING SCRAPE (Max Pages: {max_pages}) ---")

        new_collected_data = []
        stop_scraping = False
        empty_streak = 0
        
        seen_in_session = set()

        try:
            # Added check: stop if we exceed max_pages
            while not stop_scraping and len(new_collected_data) < target_count and pages_scraped_session < max_pages:
                url = self._build_url(current_page)
                html = self._fetch_html(url)

                if not html:
                    print(f"Skipping page {current_page} (no HTML).")
                    current_page += 1
                    empty_streak += 1
                    if empty_streak >= max_empty_pages:
                        print("Too many empty/no-HTML pages in a row. Stopping.")
                        break
                    continue

                soup = BeautifulSoup(html, "html.parser")

                # Cloudflare check
                page_text = soup.get_text(" ", strip=True)
                if any(s in page_text for s in ("Just a moment", "Cloudflare", "You have been blocked")):
                    print("⚠️ Looks like a Cloudflare / blocked page.")
                    break

                new_entries = self._extract_data_from_soup(soup, url)
                
                if not new_entries:
                    print(f"No entries found on page {current_page}.")
                    empty_streak += 1
                    if empty_streak >= max_empty_pages:
                        break
                    current_page += 1
                    continue

                empty_streak = 0
                added_on_page = 0

                for e in new_entries:
                    # 1. CHECK STOP CONDITION (Date Match)
                    if self.latest_stored_date and e.get("raw_date") == self.latest_stored_date:
                        print(f"Found overlap with existing raw data date ({self.latest_stored_date}). Stopping scrape.")
                        stop_scraping = True
                        break

                    # 2. Add to new list
                    sig = (e.get("raw_inst"), e.get("raw_prog"), str(e.get("raw_text"))[:50])
                    if sig not in seen_in_session:
                        seen_in_session.add(sig)
                        new_collected_data.append(e)
                        added_on_page += 1

                print(f"Pg {current_page} | New Entries: {added_on_page} | Session Total: {len(new_collected_data)}")
                
                if stop_scraping:
                    break

                current_page += 1
                pages_scraped_session += 1
            
            if pages_scraped_session >= max_pages:
                print(f"Reached page limit of {max_pages}. Stopping.")

        except KeyboardInterrupt:
            print("Scraping stopped by user.")
        except Exception as e:
            print(f"Critical Error: {e}")
        
        # Merge new data on top of old raw data (keeping raw_applicant_data.json updated too)
        print(f"Merging {len(new_collected_data)} new raw entries with {len(self.raw_data)} existing raw entries.")
        self.raw_data = new_collected_data + self.raw_data
        
        self.save_raw_data()
        return self.raw_data

    def _extract_data_from_soup(self, soup, url):
        entries = []
        rows = soup.find_all("tr")
        if not rows:
            return entries

        current_entry = None
        
        date_re = re.compile(r"\d{1,2}\s+[A-Za-z]{3}\s+\d{4}")
        decision_re = re.compile(r"(Accepted|Rejected|Wait listed|Waitlisted|Interview)", re.IGNORECASE)

        for row in rows:
            cells = row.find_all("td")
            is_main_row = False

            if len(cells) >= 2:
                if row.find("div", class_=lambda x: x and "font-medium" in x):
                    is_main_row = True
                elif len(cells[0].get_text(strip=True)) > 2:
                    is_main_row = True

            if is_main_row:
                if current_entry:
                    current_entry["raw_comments"] = re.sub(r"\s+", " ", current_entry["raw_comments"]).strip()
                    current_entry["raw_text"] = re.sub(r"\s+", " ", current_entry["raw_text"]).strip()
                    entries.append(current_entry)

                school = cells[0].get_text(strip=True)
                
                prog_block = cells[1]
                spans = prog_block.find_all("span")
                prog_text = spans[0].get_text(strip=True) if len(spans) > 0 else ""
                degree_text = spans[-1].get_text(strip=True) if len(spans) > 1 else "Other"

                full_row_text = row.get_text(" ", strip=True)

                match = decision_re.search(full_row_text)
                decision_hint = match.group(0) if match else ""

                found_date = ""
                for cell in cells:
                    txt = cell.get_text(" ", strip=True)
                    date_match = date_re.search(txt)
                    if date_match:
                        found_date = date_match.group(0)
                        break

                current_entry = {
                    "raw_inst": school,
                    "raw_prog": prog_text,
                    "raw_degree": degree_text,
                    "raw_text": full_row_text,
                    "raw_comments": "",
                    "url": url,
                    "raw_decision_hint": decision_hint,
                    "raw_date": found_date 
                }

            elif current_entry:
                row_clean = re.sub(r"\s+", " ", row.get_text(" ", strip=True))
                if row_clean:
                    current_entry["raw_text"] += " " + row_clean

                comment_p = row.find("p")
                if comment_p:
                    txt = comment_p.get_text(strip=True)
                    if txt:
                        current_entry["raw_comments"] += " " + txt

        if current_entry:
            current_entry["raw_comments"] = re.sub(r"\s+", " ", current_entry["raw_comments"]).strip()
            current_entry["raw_text"] = re.sub(r"\s+", " ", current_entry["raw_text"]).strip()
            entries.append(current_entry)

        return entries

    def save_raw_data(self):
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.raw_data, f, indent=2, ensure_ascii=False)
            print(f"Saved total {len(self.raw_data)} entries to {self.output_file}")
        except Exception as e:
            print(f"Error saving: {e}")

if __name__ == "__main__":
    # 1. Determine Max Pages based on whether applicant_data.json exists
    max_pages_limit = 10000 # Default to high number (fresh scrape)
    
    try:
        # Check if the final cleaned file exists
        base_dir = __file__.rsplit("\\", 1)[0]
        applicant_path = base_dir + "\\..\\applicant_data.json"
        with open(applicant_path, "r", encoding="utf-8") as f:
            # If we can open it, it exists. We only want recent updates.
            print("Existing 'applicant_data.json' found. Limiting scrape to 5 pages.")
            max_pages_limit = 5
    except FileNotFoundError:
        print("'applicant_data.json' not found. Performing full scrape.")
        max_pages_limit = 10000
    except Exception:
        # If empty or corrupt, do full scrape
        max_pages_limit = 10000

    # 2. Run Scraper
    scraper = GradCafeScraper(output_file="raw_applicant_data.json", debug=True)
    scraper.scrape_data(target_count=50000, max_pages=max_pages_limit)
    
    # 3. Push to Clean.py (Append Logic)
    if DataCleaner:
        print("\n--- Pushing to Clean.py ---")
        cleaner = DataCleaner()
        cleaner.update_and_merge()
        print("--- Update Complete ---")
