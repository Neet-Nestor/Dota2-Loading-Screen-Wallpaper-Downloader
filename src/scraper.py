import requests
from bs4 import BeautifulSoup


def scrape(updateProgress):
    domain = "https://dota2.fandom.com"
    base_url = "https://dota2.fandom.com/wiki/Loading_Screen"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find_all("table")[-1]
    row = table.find_all("tr")[2]
    cell = row.find_all("td")[1]

    pages = [(a["title"], a["href"]) for a in cell.find_all("a")]
    links = []

    for i, page in enumerate(pages):
        updateProgress(int(i * 100.0 / len(pages)))

        response = requests.get(domain + page[1])
        soup = BeautifulSoup(response.content, "html.parser")

        gallery = soup.find("ul", class_="gallery")
        if not gallery:
            continue

        li_list = gallery.find_all("li", class_="gallerybox")
        if not li_list:
            continue

        hrefs = [
            li.find("a", class_="image")["href"]
            for li in li_list
            if li.find("a", class_="image")
        ]

        links.extend(hrefs)

    return links
