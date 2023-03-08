import sys
import queue
import logging

import downloader
import scraper

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QComboBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

logging.basicConfig(filename="app.log", level=logging.DEBUG)

ratio_selections = ["全部", "16x9", "16x10", "4x3"]


class Dota2LoadingScreenDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.link_queue = queue.Queue()
        self.ratio = None

    def initUI(self):
        # Set window properties
        self.setGeometry(100, 100, 400, 200)
        self.setWindowTitle("Dota2加载界面壁纸下载器")

        # Create widgets
        self.folder_label = QLabel("目标文件夹：", self)

        self.folder_button = QPushButton("选择文件夹", self)
        self.folder_button.clicked.connect(self.selectFolder)

        ratio_label = QLabel("壁纸比例：", self)
        self.ratio_combobox = QComboBox(self)
        self.ratio_combobox.addItems(ratio_selections)
        self.ratio_combobox.currentIndexChanged.connect(self.ratioSelected)

        self.download_button = QPushButton("开始下载", self)
        self.download_button.clicked.connect(self.startScrape)

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: black;")

        self.scrape_layout = QHBoxLayout()
        self.scrape_labels = (
            QLabel("页面总数: 0", self),
            QLabel("爬取页面: 0", self),
            QLabel("跳过爬取: 0", self),
            QLabel("爬取壁纸总数: 0", self),
        )
        for label in self.scrape_labels:
            label.setVisible(False)
            self.scrape_layout.addWidget(label)

        self.download_layout = QHBoxLayout()
        self.download_labels = (
            QLabel("已下载壁纸: 0", self),
            QLabel("下载失败: 0", self),
        )
        for label in self.download_labels:
            label.setVisible(False)
            self.download_layout.addWidget(label)

        credit_label = QLabel("Created by @NeetNestor", self)
        version_label = QLabel("v1.1", self)
        credit_label.setStyleSheet("color: #808080;")
        version_label.setStyleSheet("color: #808080;")

        layout = QVBoxLayout()
        layout.addWidget(self.folder_label)
        layout.addWidget(self.folder_button)
        layout.addWidget(ratio_label)
        layout.addWidget(self.ratio_combobox)
        layout.addWidget(self.download_button)
        layout.addWidget(self.status_label)
        layout.addLayout(self.scrape_layout)
        layout.addLayout(self.download_layout)
        layout.addWidget(version_label)
        layout.addWidget(credit_label)

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

    def ratioSelected(self, ratio_index):
        self.ratio = ratio_selections[ratio_index] if ratio_index > 0 else None

    def startScrape(self):
        # Check if folder has been selected
        if not hasattr(self, "folder"):
            self.status_label.setText("请先选择目标文件夹")
            self.status_label.setStyleSheet("color: red;")
            return

        # Update status
        self.status_label.setText("爬取壁纸中...")
        self.status_label.setStyleSheet("color: black;")
        for label in self.scrape_labels:
            label.setVisible(True)

        # Create a scraper thread and start it
        self.thread = ScraperThread(self.link_queue, self.ratio)

        self.thread.totalPages.connect(
            lambda n: self.scrape_labels[0].setText(f"页面总数: {n}")
        )
        self.thread.pages.connect(lambda n: self.scrape_labels[1].setText(f"爬取页面: {n}"))
        self.thread.skipPages.connect(
            lambda n: self.scrape_labels[2].setText(f"跳过爬取: {n}")
        )
        self.thread.images.connect(
            lambda n: self.scrape_labels[3].setText(f"爬取壁纸总数: {n}")
        )
        self.thread.finished.connect(self.scrapeFinished)
        self.thread.start()

        # Show progress bar and hide download button
        self.folder_button.setEnabled(False)
        self.download_button.setVisible(False)
        self.ratio_combobox.setEnabled(False)

    def scrapeFinished(self):
        # Update status
        self.status_label.setText("下载壁纸中...")
        self.status_label.setStyleSheet("color: black;")
        for label in self.download_labels:
            label.setVisible(True)

        # Create a scraper thread and start it
        self.thread = DownloaderThread(self.link_queue, self.folder)
        self.thread.downloaded.connect(
            lambda n: self.download_labels[0].setText(f"已下载壁纸: {n}")
        )
        self.thread.failed.connect(
            lambda n: self.download_labels[1].setText(f"下载失败: {n}")
        )
        self.thread.finished.connect(self.downloadFinished)
        self.thread.start()

    def downloadFinished(self):
        # Hide progress bar and show download button
        self.folder_button.setEnabled(True)
        self.download_button.setVisible(True)
        self.ratio_combobox.setEnabled(True)

        self.status_label.setText("下载完成")


class ScraperThread(QThread):
    # Define a custom signal that will be emitted during the scrape process
    totalPages = pyqtSignal(int)
    pages = pyqtSignal(int)
    skipPages = pyqtSignal(int)
    images = pyqtSignal(int)

    def __init__(self, result_queue: queue.Queue, ratio):
        super().__init__()
        self.result_queue = result_queue
        self.ratio = ratio

    def run(self):
        links = scraper.scrape(
            self.totalPages, self.pages, self.skipPages, self.images, self.ratio
        )
        print(links)
        for link in links:
            print(link)
            self.result_queue.put(link)


class DownloaderThread(QThread):
    # Define a custom signal that will be emitted during the download process
    downloaded = pyqtSignal(int)
    failed = pyqtSignal(int)

    def __init__(self, task_queue: queue.Queue, folder):
        super().__init__()
        self.task_queue = task_queue
        self.task_count, self.failed_count = 0, 0
        self.total_task = task_queue.qsize()
        self.folder = folder

    def run(self):
        while not self.task_queue.empty():
            link = self.task_queue.get()
            try:
                downloader.download(link, self.folder)
                self.task_queue.task_done()
                self.task_count += 1
                self.downloaded.emit(self.task_count)
            except:
                self.failed.emit(int((self.task_count) * 100.0 / self.total_task))
                self.failed_count += 1
                self.failed.emit(self.failed_count)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("dota2.png"))
    window = Dota2LoadingScreenDownloader()
    sys.exit(app.exec())
