#!/usr/bin/env python3

import os
import json
import logging
import re
import sys
import time
import requests
from typing import Dict
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from atlassian import Confluence
import yaml


class ConfluenceSnapshot:

    LAZY_TIMEOUT = 10
    WEBLOAD_TIMEOUT = 120
    SCRIPT_TIMEOUT = 120

    def __init__(self, config: Dict) -> None:
        """Initialize ConfluenceSnapshot with provided credentials and download path.

        Args:
            config (Dict): Configuration dictionary containing Confluence credentials and settings.
        """
        self.config = config
        self.api = Confluence(username=config['username'], password=config['password'], url=config['api_url'])
        self.download_path = Path(config['download_path'])
        self._init_logger()

    def _init_logger(self) -> None:
        """Initialize logger for logging download progress."""
        self.logger = logging.getLogger("Confluence Downloader")
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s', datefmt='%H:%M:%S')
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def download_space_pages(self) -> None:
        """Download pages from a specified Confluence space recursively."""
        self.page_counter = 1
        home_page_id = self.api.get_space(self.config['space'])['homepage']['id']
        self._download_page_tree(home_page_id, self.download_path)

    def _download_page_tree(self, parent_id: int, download_path: Path) -> None:
        """Recursively download pages from Confluence.

        Args:
            parent_id (int): The ID of the parent page to start downloading from.
            download_path (Path): The path where downloaded pages will be saved.
        """
        for child in list(self.api.get_child_pages(parent_id)):
            child['title'] = re.sub(r'[^\w_. -]', '_', child['title'])  # remove bad characters from page title
            new_download_path = download_path.joinpath(child['title'])
            self.logger.info(f"{self.page_counter} Downloading page '{child['title']}' to {new_download_path}")
            self._download_page(child, download_path)
            if self.config.get('lazy_mode'):
                self.logger.debug(f"Lazy sleep {self.LAZY_TIMEOUT}s")
                time.sleep(self.LAZY_TIMEOUT)
            if self.config.get('with_attachments'):
                self._download_attachments(child, new_download_path)
            self.page_counter += 1
            children = list(self.api.get_child_pages(child['id']))
            if children:
                new_download_path.mkdir(exist_ok=True)
                self._download_page_tree(child['id'], new_download_path)
            new_download_path = new_download_path.parent

    def _download_page(self, page: Dict[str,str], download_path: Path) -> None:
        """Download a page from Confluence.

        Args:
            page (Dict): The page (API dict) to download.
            download_path (Path): The path where downloaded pages will be saved.
        """
        if download_path.joinpath(str(page['title']) + '.pdf').exists():
            self.logger.warning(f"Page with title '{page['title']}' already downloaded, skipping")
            return
        options = self._get_chrome_options(download_path=download_path)
        driver = webdriver.Chrome(options=options)
        driver.get(f"{self.config['web_url']}/{page['_links']['webui']}")
        driver.implicitly_wait(self.WEBLOAD_TIMEOUT)
        driver.set_script_timeout(self.SCRIPT_TIMEOUT)  # printing preview may take more time than default timeout
        driver.execute_script('window.print();')
        driver.quit()
        self._rename_latest_downloaded_page(page, download_path)

    def _rename_latest_downloaded_page(self, page: Dict[str, str], download_path: Path) -> None:
        """Rename the latest downloaded page.

        Args:
            page: The page information.
            download_path (Path): The path where downloaded pages are saved.
        """
        latest_filepath = max(download_path.glob('*.pdf'), key=lambda x: x.stat().st_ctime)
        renamed_filepath = Path(str(latest_filepath.with_name(page['title'])) + '.pdf')
        latest_filepath.rename(renamed_filepath)
        self.logger.info(f"Renamed '{latest_filepath.name}' -> '{renamed_filepath.name}'")

    def _download_attachments(self, page: Dict[str,str], download_path: Path) -> None:
        """Download attachments from a page.

        Args:
            page (Dict): The page (API dict) to download attachments from.
            download_path (Path): The path where downloaded attachments will be saved.
        """
        attachments = self.api.get_attachments_from_content(page_id=page['id'])['results']
        if not attachments:
            self.logger.debug(f"No attachments found on page '{page['title']}'")
            return
        # use separate directory for attachments near downloaded page
        download_path = download_path.parent.joinpath(page['title']+'.attachments')
        download_path.mkdir(exist_ok=True)
        self.logger.info(f"Downloading {len(attachments)} attachments on page '{page['title']}'")
        for attachment in attachments:
                filename = attachment['title']
                if os.path.isfile(download_path.joinpath(filename)):
                    self.logger.warning(f"File {filename} already exists, skipping")
                    continue
                download_link = self.api.url + attachment['_links']['download']
                r = requests.get(download_link, auth=(self.api.username, self.api.password))
                if r.status_code == 200:
                    with open(download_path.joinpath(filename), "wb") as f:
                        for bits in r.iter_content(): f.write(bits)
                    self.logger.info(f"Downloaded attachment '{filename}'")
                else:
                    self.logger.error(f"Cannot download attachment {filename}")

                if self.config.get('lazy_mode'):
                    self.logger.debug(f"Lazy sleep {self.LAZY_TIMEOUT}s")
                    time.sleep(self.LAZY_TIMEOUT)

    def _get_chrome_options(self, with_print_options: bool=True, download_path: Path = None) -> webdriver.ChromeOptions:
        """Configure Chrome options for printing pages.

        Args:
            with_print_options (bool): add printing option with 'download_path' to global options
            download_path (Path): The path where downloaded pages will be saved.

        Returns:
            webdriver.ChromeOptions: Chrome options for printing pages.
        """
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.config['user_data_dir']}")
        options.add_argument(f"--profile-directory={self.config['profile_directory']}")
        options.add_argument('--kiosk-printing')
        if with_print_options:
            print_options = self._get_print_options(download_path)
            options.add_experimental_option('prefs', print_options)
        return options

    def _get_print_options(self, download_path: Path) -> Dict:
        """Configure printing options for Chrome.

        Args:
            download_path (Path): The path where downloaded pages will be saved.

        Returns:
            Dict: options
        """
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
        print_options = {
            'printing.print_preview_sticky_settings.appState': json.dumps(app_state),
            'savefile.default_directory': str(download_path)
        }
        return print_options

    def verify_settings(self):
        self.logger.debug("Verifying profile path")
        profile_path = Path(self.config['user_data_dir']).joinpath(self.config['profile_directory'])
        if not profile_path.exists():
            self.logger.error(f"Profile path {profile_path} doesn't exist")
            sys.exit(1)

        self.logger.debug("Verifying API credentials")
        try:
            _ = self.api.get_space(self.config['space'])
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Cannot login to Confluence API: {e}")
            sys.exit(1)

        self.logger.debug("Verifying web credentials")
        options = self._get_chrome_options(with_print_options=False)
        driver = webdriver.Chrome(options=options)
        driver.get(f"{self.config['web_url']}")
        try:
            driver.find_element(By.ID, 'header')
        except NoSuchElementException:
            self.logger.warning("You need to login Confluence first and then press enter")
            input('[Enter]')

if __name__ == "__main__":

    config = yaml.load(
        open(Path(__file__).parent.resolve().joinpath('config.yaml'), 'r'),
        Loader=yaml.FullLoader)
    downloader = ConfluenceSnapshot(config)
    if config.get('verify_settings'):
        downloader.verify_settings()
    downloader.download_space_pages()
