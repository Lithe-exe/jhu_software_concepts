from board.scrape import GradCafeScraper
from board.clean import DataCleaner

def main():
    # 1. Scrape
    scraper = GradCafeScraper(output_file="raw_applicant_data.json")
    raw_data = scraper.scrape_data(target_count=30001)
    scraper.save_raw_data()
    
    # 2. Clean
    cleaner = DataCleaner(input_file="raw_applicant_data.json", output_file="cleaned_applicant_data.json")
    cleaner.clean_data(raw_data)
    cleaner.save_data()

if __name__ == "__main__":
    main()