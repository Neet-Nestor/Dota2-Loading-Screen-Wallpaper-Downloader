import requests
import os.path
import logging


def download(link, destinationFolder):
    logging.info(
        f"[Downloader] Start downloading {link} into folder {destinationFolder} ..."
    )

    for part in link.split("/"):
        if ".png" in part or ".jpg" in part or ".jpeg" in part:
            file_name = part
            break

    response = requests.get(link)

    with open(
        os.path.join(destinationFolder, file_name),
        "wb",
    ) as f:
        f.write(response.content)
