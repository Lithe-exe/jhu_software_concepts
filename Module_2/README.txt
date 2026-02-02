Sultan Jacobs 
JHU ID: B443F8
Module Info: Module 2 Web Scraping| Due 02/01/25 @ 11:59 PM EST 
Approach: Understanding the ROBOT.txt file for the target website allows webscraping I proceeded in this manner
Using the setup of the HTMl on the target website I have the code go through each page by incrementing the value of each page in the url format as it scrapes the individual entries nested in the HTML.
Each entry follows the same format and knowing that I have the code parse through the selected key notes and extract that data as it is within the html.
I create a JSON file that is written to, a python list that holds the scraped entries and a pool manager for my HTTP client
With this setup when an error comes up during the feeding of my raw data into the output there is an autosave feature allowing the scraping to continue from where it left off.
To handle timeouts and cloudflare errors there's a built in buffer using PoolManager with a retry allowing continuation of scraping even when running into an issue.

The main flow is going through the base url then getting webpage html & deciding the start point of the scraping based on if there is already an existing file or not where in it will check for duplicates 
based on the individual signature of each array. Then parse with beautifulsoup4, extract from soup, add non duplicates, save every certain amount of pages & tracks the amount of times nothing has been added
which I found indicates some sort of block so after 10 blocks it stops and reruns again to avoid an infinite loop. 
Each piece of data is tied directly to a value in a standard dictionary written in my code and it appends by having the the same order of data information on the website formatted and changing the entry in this code according to the 
order of it on the website. After all this is done it is saved to a JSON file. 

There is also a file called entrycheck.py here to compare how many entries are in the raw data vs the clean data pre llm


Known Bugs: 1. Main.py when run will go through some pages at time without getting any data but that is dependent on cloudflare and errors blocking scraping/excessive requests. 
By design after enough failed attempts I do have it just move on but if I were to have the time to fix it I would just change the way my current code saves.
Rather than continuing past a page that does have data but can't be accessed I would have it stop and save current data then load into that same page again 
but this could cause a problem with infinite loops thus timeouts with no data. 
Using a module that mimics human webpage interaction would be the most solid way to fix this error I imagine.

**Instructions**
Run main.py after installing all requirements under module 2 folder and wait for the scraped & cleaned files to populate. 
Install all requirements in the llm_hosting folder & make sure you have python>=3.10, <=3.12 as later environments may not have support for all the imported modules.
Then run the app.py 