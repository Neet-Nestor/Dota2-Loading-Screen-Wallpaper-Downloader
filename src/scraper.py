import requests
from bs4 import BeautifulSoup
import logging


def scrape(
    totalPages_progress, pages_progress, skipPages_progress, images_progress, ratio
):
    logging.info(f"[Scraper] Start scraping...")

    domain = "https://dota2.fandom.com"
    base_url = "https://dota2.fandom.com/wiki/Loading_Screen"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find_all("table")[-1]
    row = table.find_all("tr")[2]
    cell = row.find_all("td")[1]

    pages = [(a["title"], a["href"]) for a in cell.find_all("a")]
    links = []
    logging.info(f"[Scraper] pages length: {len(pages)}")
    totalPages_progress.emit(len(pages))

    page_count, skip_count, image_count = 0, 0, 0

    for page in pages:
        response = requests.get(domain + page[1])
        soup = BeautifulSoup(response.content, "html.parser")

        gallery = soup.find("ul", class_="gallery")
        if not gallery:
            logging.warning(f"[Scraper] Page '{page[0]}' has no 'ul.gallery'", page[1])
            skip_count += 1
            skipPages_progress.emit(skip_count)
            continue

        li_list = gallery.find_all("li", class_="gallerybox")
        if not li_list:
            logging.warning(
                f"[Scraper] Page '{page[0]}' has no 'li.gallerybox'", page[1]
            )
            skip_count += 1
            skipPages_progress.emit(skip_count)
            continue

        hrefs = [
            li.find("a", class_="image")["href"]
            for li in li_list
            if li.find("a", class_="image")
            and (ratio is None or ratio in li.find("a", class_="image")["href"])
        ]
        logging.info(
            f"[Scraper] Page '{page[0]}' has {len(hrefs)} images with ratio {ratio}",
            hrefs,
        )

        links.extend(hrefs)

        page_count += 1
        image_count += len(hrefs)

        pages_progress.emit(page_count)
        images_progress.emit(image_count)

    logging.info(f"[Scraper] Total {len(links)} links found")
    return links
