import sys
import queue

import downloader
import scraper

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QProgressBar,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon


class Dota2LoadingScreenDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.link_queue = queue.Queue()

    def initUI(self):
        # Set window properties
        self.setGeometry(100, 100, 400, 200)
        self.setWindowTitle("Dota2加载界面壁纸下载器")

        # Create widgets
        self.folder_label = QLabel("目标文件夹：", self)

        self.folder_button = QPushButton("选择文件夹", self)
        self.folder_button.clicked.connect(self.selectFolder)

        self.download_button = QPushButton("开始下载", self)
        self.download_button.clicked.connect(self.startScrape)

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: black;")

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(20, 130, 360, 30)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.folder_label)
        layout.addWidget(self.folder_button)
        layout.addWidget(self.download_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        # Show window
        self.setLayout(layout)
        self.show()

    def selectFolder(self):
        # Open file dialog to select a folder
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        self.folder_label.setText("目标文件夹：" + folder)
        self.status_label.setText("")
        self.status_label.setStyleSheet("color: black;")
        self.folder = folder

    def startScrape(self):
        # Check if folder has been selected
        if not hasattr(self, "folder"):
            self.status_label.setText("请先选择目标文件夹")
            self.status_label.setStyleSheet("color: red;")
            return

        # Update status
        self.status_label.setText("爬取壁纸中...")
        self.status_label.setStyleSheet("color: black;")

        # Create a scraper thread and start it
        self.thread = ScraperThread(self.link_queue)
        self.thread.scrapeProgress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.scrapeFinished)
        self.thread.start()

        # Show progress bar and hide download button
        self.progress_bar.setVisible(True)
        self.folder_button.setEnabled(False)
        self.download_button.setVisible(False)

    def scrapeFinished(self):
        # Update status
        self.status_label.setText("下载壁纸中...")
        self.status_label.setStyleSheet("color: black;")

        # Create a scraper thread and start it
        self.thread = DownloaderThread(self.link_queue, self.folder)
        self.thread.downloadProgress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.downloadFinished)
        self.thread.start()

    def downloadFinished(self):
        # Hide progress bar and show download button
        self.progress_bar.setVisible(False)
        self.folder_button.setEnabled(True)
        self.download_button.setVisible(True)

        self.status_label.setText("下载完成")


class ScraperThread(QThread):
    # Define a custom signal that will be emitted during the scrape process
    scrapeProgress = pyqtSignal(int)

    def __init__(self, result_queue: queue.Queue):
        super().__init__()
        self.result_queue = result_queue

    def run(self):
        links = scraper.scrape(lambda progress: self.scrapeProgress.emit(progress))
        print(links)
        for link in links:
            print(link)
            self.result_queue.put(link)


class DownloaderThread(QThread):
    # Define a custom signal that will be emitted during the download process
    downloadProgress = pyqtSignal(int)

    def __init__(self, task_queue: queue.Queue, folder):
        super().__init__()
        self.task_queue = task_queue
        self.task_count = 0
        self.total_task = task_queue.qsize()
        self.folder = folder

    def run(self):
        while not self.task_queue.empty():
            link = self.task_queue.get()
            downloader.download(link, self.folder)
            self.task_queue.task_done()
            self.task_count += 1
            self.downloadProgress.emit(int((self.task_count) * 100.0 / self.total_task))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("dota2.png"))
    window = Dota2LoadingScreenDownloader()
    sys.exit(app.exec())
