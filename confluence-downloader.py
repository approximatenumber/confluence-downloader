#!/usr/bin/env python3

import os
import json
import logging
import sys
import time
import requests
from typing import Dict
from pathlib import Path
from selenium import webdriver
from atlassian import Confluence
import yaml


class ConfluenceDownloader:

    LAZY_TIMEOUT = 10

    def __init__(self, config: Dict) -> None:
        """Initialize ConfluenceDownloader with provided credentials and download path.

        Args:
            config (Dict): Configuration dictionary containing Confluence credentials and settings.
        """
        self.config = config
        self.client = Confluence(username=config['username'], password=config['password'], url=config['api_url'])
        self.prefix = Path(config['download_path'])
        self._init_logger()

    def _init_logger(self) -> None:
        """Initialize logger for logging download progress."""
        self.logger = logging.getLogger("Confluence Downloader")
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s', datefmt='%H:%M:%S')
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def download_space_pages(self) -> None:
        """Download pages from a specified Confluence space recursively."""
        self.page_counter = 1
        home_page_id = self.client.get_space(self.config['space'])['homepage']['id']
        self._download_page_tree(home_page_id, self.prefix)

    def _download_page_tree(self, parent_id: int, prefix: Path) -> None:
        """Recursively download pages from Confluence.

        Args:
            parent_id (int): The ID of the parent page to start downloading from.
            prefix (Path): The path where downloaded pages will be saved.
        """
        for child in self.client.get_child_pages(parent_id):
            new_prefix = prefix.joinpath(child['title'])
            os.makedirs(new_prefix, exist_ok=True)
            self.logger.info(f"{self.page_counter} Downloading page '{child['title']}' to {new_prefix}")
            self._download_page(child, prefix)
            if self.config.get('with_attachments'):
                self._download_attachments(child, new_prefix)
            self.page_counter += 1
            if self.client.get_child_pages(child['id']):
                self._download_page_tree(child['id'], new_prefix)
            new_prefix = new_prefix.parent
            if self.config.get('lazy_mode'):
                time.sleep(self.LAZY_TIMEOUT)

    def _download_page(self, page: Dict[str,str], prefix: Path) -> None:
        """Download a page from Confluence.

        Args:
            page (Dict): The page (API dict) to download.
            prefix (Path): The path where downloaded pages will be saved.
        """
        if prefix.joinpath(str(page['title']) + '.pdf').exists():
            self.logger.warning(f"Page with title '{page['title']}' already downloaded, skipping")
            return
        options = self._configure_chrome_options(prefix)
        driver = webdriver.Chrome(options=options)
        driver.get(f"{self.config['web_url']}/{page['_links']['webui']}")
        driver.implicitly_wait(60)
        driver.execute_script('window.print();')
        driver.quit()
        self._rename_latest_downloaded_page(page, prefix)

    def _rename_latest_downloaded_page(self, page, prefix):
        """Rename the latest downloaded page.

        Args:
            page: The page information.
            prefix (Path): The path where downloaded pages are saved.
        """
        latest_filepath = max(prefix.glob('*.pdf'), key=lambda x: x.stat().st_ctime)
        renamed_filepath = Path(str(latest_filepath.with_name(page['title'])) + '.pdf')
        latest_filepath.rename(renamed_filepath)
        self.logger.info(f"Renamed '{latest_filepath.name}' -> '{renamed_filepath.name}'")

    def _download_attachments(self, page: Dict[str,str], prefix: Path) -> None:
        """Download attachments from a page.

        Args:
            page (Dict): The page (API dict) to download attachments from.
            prefix (Path): The path where downloaded attachments will be saved.
        """
        attachments = self.client.get_attachments_from_content(page_id=page['id'])['results']
        if not attachments:
            self.logger.debug(f"No attachments found on page '{page['title']}'")
            return
        self.logger.info(f"Downloading {len(attachments)} attachments on page '{page['title']}'")
        for attachment in attachments:
                filename = attachment['title']
                if os.path.isfile(prefix.joinpath(filename)):
                    self.logger.warning(f"File {filename} already exists, skipping")
                    continue
                download_link = self.client.url + attachment['_links']['download']
                r = requests.get(download_link, auth=(self.client.username, self.client.password))
                if r.status_code == 200:
                    with open(prefix.joinpath(filename), "wb") as f:
                        for bits in r.iter_content(): f.write(bits)
                    self.logger.info(f"Downloaded attachment '{filename}'")
                else:
                    self.logger.error(f"Cannot download attachment {filename}")

                if self.config.get('lazy_mode'):
                    time.sleep(self.LAZY_TIMEOUT)

    def _configure_chrome_options(self, prefix: Path) -> webdriver.ChromeOptions:
        """Configure Chrome options for printing pages.

        Args:
            prefix (Path): The path where downloaded pages will be saved.

        Returns:
            webdriver.ChromeOptions: Chrome options for printing pages.
        """
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.config['user_data_dir']}")
        options.add_argument(f"--profile-directory={self.config['profile_directory']}")
        options.add_argument("--start-maximized")
        options.add_argument('--kiosk-printing')
        app_state = {
            "recentDestinations": [
                {
                    "id": "Save as PDF",
                    "origin": "local",
                    "account": ""
                }
            ],
            "selectedDestinationId": "Save as PDF",
            "version": 2,
            "isLandscapeEnabled": True,
            "isHeaderFooterEnabled": False
        }
        profile = {
            'printing.print_preview_sticky_settings.appState': json.dumps(app_state),
            'savefile.default_directory': str(prefix)
        }
        options.add_experimental_option('prefs', profile)
        return options


if __name__ == "__main__":

    config = yaml.load(
        open(Path(__file__).parent.resolve().joinpath('config.yml'), 'r'),
        Loader=yaml.FullLoader)
    downloader = ConfluenceDownloader(config)
    downloader.download_space_pages()
