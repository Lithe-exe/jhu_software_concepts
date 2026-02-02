import json
import re
import urllib3
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup


class GradCafeScraper:
    BASE_URL = "https://www.thegradcafe.com/survey/index.php"

    def __init__(self, output_file="raw_applicant_data.json", debug=True):
        self.output_file = output_file
        self.debug = debug
        self.raw_data = []
        self.http = self._setup_http()

        # AUTO-RESUME LOGIC 
        try:
            with open(self.output_file, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)
            if not isinstance(self.raw_data, list):
                raise ValueError("JSON root is not a list")
            print(f"Loaded {len(self.raw_data)} existing entries. Resuming scrape...")
        except FileNotFoundError:
            print("No existing file found. Starting fresh.")
            self.raw_data = []
        except Exception:
            print("Existing JSON is corrupt/empty or invalid. Starting fresh.")
            self.raw_data = []

    def _setup_http(self):
       # Timeouts and Retries in case of cloudfare or transient issues 
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
        # Creates URL for a given page number| Critical for continuing pagination
        # q=* (search all), t=a (all results), page=page_number
        return f"{self.BASE_URL}?q=%2A&t=a&o=&page={page}"

    def _fetch_html(self, url: str) -> str | None:
         # Fetches HTML content from a URL with proper headers
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            # Important: ask for uncompressed so we don't accidentally decode garbage
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
            "Referer": "https://www.thegradcafe.com/",
        }

        try:
            # preload_content=False lets us decode properly via read(decode_content=True)
            r = self.http.request("GET", url, headers=headers, preload_content=False)

            raw = r.read(decode_content=True)
            text = raw.decode("utf-8", errors="replace")

            if self.debug:
                ctype = r.headers.get("content-type")
                cenc = r.headers.get("content-encoding")
                print(f"[DEBUG] HTTP {r.status} | CT={ctype} | CE={cenc} | {url}")
                snippet = re.sub(r"\s+", " ", text[:400]).strip()
                print(f"[DEBUG] SNIPPET: {snippet}")

            # Treat hard errors as no HTML
            if r.status >= 400 and r.status != 429:
                print(f"HTTP {r.status} for {url}")
                return None

            return text
        except Exception as e:
            print(f"Request failed for {url}: {e}")
            return None
    # Scrapes data until target count is met or too many empty pages encountered. Resumes from existing data if target count is not met prior to stopping.
    def scrape_data(self, target_count=50000, save_every_pages=8, max_empty_pages=10):
        """
        Scrape until target_count or until we hit too many consecutive empty pages.
        """
        # Determine starting page. Each page has ~20 entries when I counted 01/28/25.
        if len(self.raw_data) > 0:
            current_page = max(1, (len(self.raw_data) // 20) + 1)
        else:
            current_page = 1

        print(f"--- STARTING SCRAPE AT PAGE {current_page} ---")

        # Signature set for deduplication
        seen = set()
        for e in self.raw_data:
            sig = (e.get("raw_inst"), e.get("raw_prog"), str(e.get("raw_text"))[:50])
            seen.add(sig)

        empty_streak = 0
        # Main scraping loop
        try:
            while len(self.raw_data) < target_count:
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

                # Cloudflare / block page detection (common strings)
                page_text = soup.get_text(" ", strip=True)
                if any(
                    s in page_text
                    for s in (
                        "Just a moment",
                        "Checking your browser",
                        "Attention Required",
                        "Cloudflare",
                        "You have been blocked",
                    )
                ):
                    print("⚠️ Looks like a Cloudflare / blocked page, not real results.")
                     # If cloudFlare is blocking then end the scrape here
                    if self.debug:
                        print("[DEBUG] BLOCK PAGE TEXT (first 300):")
                        print(re.sub(r"\s+", " ", page_text[:300]).strip())
                    break

                # Structure check
                if self.debug:
                    print(
                        f"[DEBUG] tr={len(soup.find_all('tr'))}, td={len(soup.find_all('td'))}, "
                        f"div={len(soup.find_all('div'))}"
                    )

                new_entries = self._extract_data_from_soup(soup, url)
                # Handle empty page but is a patchwork code as there shouldn't be any empty pages in normal operation. Catch all for blocs I can't predict.
                if not new_entries:
                    print(f"No entries found on page {current_page}.")
                    empty_streak += 1
                    if empty_streak >= max_empty_pages:
                        print("Too many empty pages in a row. Stopping.")
                        break
                    current_page += 1
                    continue

                empty_streak = 0

                # Deduplicate and Append to avoid duplicates & skewing data
                added_count = 0
                for e in new_entries:
                    sig = (e.get("raw_inst"), e.get("raw_prog"), str(e.get("raw_text"))[:50])
                    if sig in seen:
                        continue
                    seen.add(sig)
                    self.raw_data.append(e)
                    added_count += 1

                print(f"Pg {current_page} | Added: {added_count} | Total: {len(self.raw_data)}")

                current_page += 1

                # Incremental Save
                if current_page % save_every_pages == 0:
                    self.save_raw_data()

        except KeyboardInterrupt:
            print("Scraping stopped by user.")
        except Exception as e:
            print(f"Critical Error: {e}")
        finally:
            self.save_raw_data()

        return self.raw_data[:target_count]

    def _extract_data_from_soup(self, soup, url):
        # Heavily based on HTML structure of website. If site changes this will not work but analysis can be redone from Webdata_raw.py
        entries = []

        # Try table rows first
        rows = soup.find_all("tr")
        if not rows:
            return entries

        current_entry = None

        # Decision keywords
        decision_re = re.compile(r"(Accepted|Rejected|Wait listed|Waitlisted|Interview)", re.IGNORECASE)

        for row in rows:
            cells = row.find_all("td")
            is_main_row = False

            # Heuristic main row detection
            if len(cells) >= 2:
                
                if row.find("div", class_=lambda x: x and "font-medium" in x):
                    is_main_row = True
                elif len(cells[0].get_text(strip=True)) > 2:
                    is_main_row = True

            if is_main_row:
                # Save previous entry
                if current_entry:
                    current_entry["raw_comments"] = re.sub(r"\s+", " ", current_entry["raw_comments"]).strip()
                    current_entry["raw_text"] = re.sub(r"\s+", " ", current_entry["raw_text"]).strip()
                    entries.append(current_entry)
                # Links text from html to data fields 
                school = cells[0].get_text(strip=True)

                prog_block = cells[1]
                spans = prog_block.find_all("span")
                prog_text = spans[0].get_text(strip=True) if len(spans) > 0 else ""
                degree_text = spans[-1].get_text(strip=True) if len(spans) > 1 else "Other"

                full_row_text = row.get_text(" ", strip=True)

                match = decision_re.search(full_row_text)
                decision_hint = match.group(0) if match else ""

                current_entry = {
                    "raw_inst": school,
                    "raw_prog": prog_text,
                    "raw_degree": degree_text,
                    "raw_text": full_row_text,
                    "raw_comments": "",
                    "url": url,
                    "raw_decision_hint": decision_hint,
                }

            elif current_entry:
                # Detail row (stats or comments)
                row_clean = re.sub(r"\s+", " ", row.get_text(" ", strip=True))
                if row_clean:
                    current_entry["raw_text"] += " " + row_clean

                # Extract Comments
                comment_p = row.find("p")
                if comment_p:
                    txt = comment_p.get_text(strip=True)
                    if txt:
                        current_entry["raw_comments"] += " " + txt

        # Append final entry
        if current_entry:
            current_entry["raw_comments"] = re.sub(r"\s+", " ", current_entry["raw_comments"]).strip()
            current_entry["raw_text"] = re.sub(r"\s+", " ", current_entry["raw_text"]).strip()
            entries.append(current_entry)

        return entries

    def save_raw_data(self):
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.raw_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.raw_data)} entries to {self.output_file}")
        except Exception as e:
            print(f"Error saving: {e}")


if __name__ == "__main__":
    scraper = GradCafeScraper(output_file="raw_applicant_data.json", debug=True)
    scraper.scrape_data(target_count=50000)
    scraper.save_raw_data()
