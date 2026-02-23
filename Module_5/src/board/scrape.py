"""
Scraper Module
==============

Scrape applicant data from TheGradCafe.
"""

import json
import os
import re

import urllib3
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry


class GradCafeScraper:
    """Scrape GradCafe survey results."""

    BASE_URL = "https://www.thegradcafe.com/survey/index.php"

    def __init__(self, output_file="raw_applicant_data.json", debug=True):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(output_file):
            self.output_file = os.path.join(base_dir, output_file)
        else:
            self.output_file = output_file

        self.debug = debug
        self.raw_data = []
        self.http = self._setup_http()
        self.latest_stored_date = None

        try:
            with open(self.output_file, "r", encoding="utf-8") as file_handle:
                self.raw_data = json.load(file_handle)

            if not isinstance(self.raw_data, list):
                self.raw_data = []

            for entry in self.raw_data:
                if entry.get("raw_date"):
                    self.latest_stored_date = entry.get("raw_date")
                    break
        except (FileNotFoundError, ValueError):
            self.raw_data = []

    @staticmethod
    def _setup_http():
        """Configure urllib3 with retries."""
        retry = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        return urllib3.PoolManager(retries=retry)

    def _build_url(self, page):
        return f"{self.BASE_URL}?q=%2A&t=a&o=&page={page}"

    def _fetch_html(self, url):
        """Fetch HTML content from a URL."""
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}
        try:
            response = self.http.request("GET", url, headers=headers)
            if response.status >= 400:
                return None
            return response.data.decode("utf-8", errors="replace")
        except urllib3.exceptions.HTTPError as request_error:
            if self.debug:
                print(f"Request Error: {request_error}")
            return None

    def scrape_data(self, target_count=50000, max_pages=10000):
        """Run the main scraping loop and append fresh entries to raw data."""
        current_page = 1
        pages_scraped = 0

        if max_pages == 10000 and self.latest_stored_date:
            max_pages = 5

        print(f"--- STARTING SCRAPE (Max Pages: {max_pages}) ---")

        new_collected_data = []
        stop_scraping = False
        seen_in_session = set()

        while (
            not stop_scraping
            and len(new_collected_data) < target_count
            and pages_scraped < max_pages
        ):
            url = self._build_url(current_page)
            html = self._fetch_html(url)

            if not html:
                current_page += 1
                continue

            soup = BeautifulSoup(html, "html.parser")
            new_entries = self._extract_data_from_soup(soup, url)

            if not new_entries:
                current_page += 1
                continue

            for entry in new_entries:
                if (
                    self.latest_stored_date
                    and entry.get("raw_date") == self.latest_stored_date
                ):
                    stop_scraping = True
                    break

                sig = (
                    entry.get("raw_inst"),
                    entry.get("raw_prog"),
                    str(entry.get("raw_text"))[:50],
                )
                if sig not in seen_in_session:
                    seen_in_session.add(sig)
                    new_collected_data.append(entry)

            current_page += 1
            pages_scraped += 1

        self.raw_data = new_collected_data + self.raw_data
        self.save_raw_data()
        return self.raw_data

    def _extract_data_from_soup(self, soup, url):  # pylint: disable=too-many-locals
        """Parse HTML table rows into entry dictionaries."""
        entries = []
        rows = soup.find_all("tr")
        if not rows:
            return entries

        current_entry = None
        date_re = re.compile(r"\d{1,2}\s+[A-Za-z]{3}\s+\d{4}")

        for row in rows:
            cells = row.find_all("td")
            is_main_row = False
            if len(cells) >= 2 and len(cells[0].get_text(strip=True)) > 2:
                is_main_row = True

            if is_main_row:
                if current_entry is not None:
                    entries.append(current_entry)

                school = cells[0].get_text(strip=True)
                prog_block = cells[1].find_all("span")
                prog_text = prog_block[0].get_text(strip=True) if prog_block else ""
                full_row_text = row.get_text(" ", strip=True)

                found_date = ""
                for cell in cells:
                    text = cell.get_text(" ", strip=True)
                    date_match = date_re.search(text)
                    if date_match:
                        found_date = date_match.group(0)
                        break

                current_entry = {
                    "raw_inst": school,
                    "raw_prog": prog_text,
                    "raw_text": full_row_text,
                    "raw_comments": "",
                    "url": url,
                    "raw_date": found_date,
                }
            elif current_entry is not None:
                text = row.get_text(strip=True)
                if text:
                    current_entry["raw_comments"] += f" {text}"

        if current_entry is not None:
            entries.append(current_entry)

        return entries

    def save_raw_data(self):
        """Write raw data to JSON."""
        try:
            with open(self.output_file, "w", encoding="utf-8") as file_handle:
                json.dump(self.raw_data, file_handle, indent=2)
        except (OSError, TypeError, ValueError) as save_error:
            print(f"Error saving: {save_error}")


def main():
    """Execute a small scraping run directly."""
    scraper = GradCafeScraper()
    scraper.scrape_data(max_pages=1)


if __name__ == "__main__":
    main()
