from board.scrape import GradCafeScraper
from board.clean import DataCleaner
from board.entrycheck import check_data_counts

def main():
    # 1. Scrape
    scraper = GradCafeScraper(output_file="raw_applicant_data.json")
    raw_data = scraper.scrape_data(target_count=50000)
    scraper.save_raw_data()
    
    # 2. Clean
    cleaner = DataCleaner(input_file="raw_applicant_data.json", output_file="applicant_data.json")
    cleaner.clean_data(raw_data)
    cleaner.save_data()
    
    # 3. Last step - Checking the amount of individual entries in each file.
    check_data_counts()
if __name__ == "__main__":
    main()