import mechanicalsoup

browser = mechanicalsoup.Browser()
url = "https://www.thegradcafe.com/survey/"

page=browser.get(url)

html = page.soup.prettify()

with open("gradcafe_dump.txt", "w", encoding="utf-8") as f:
    f.write(html)

print("Current HTML setup for gradcafe generated: gradcafe_dump.txt")
