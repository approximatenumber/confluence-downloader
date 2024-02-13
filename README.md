# Confluence Downloader

Confluence Downloader is a Python application designed to download pages and attachments from a Confluence space.

## Description

Confluence Downloader uses the Confluence API to recursively download pages and their attachments from a specified Confluence space. It saves the downloaded pages as PDF files and their attachments to a specified directory.

## Requirements

- Python 3
- `selenium` library
- `atlassian` library
- `requests` library
- Google Chrome (for Selenium WebDriver)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/your-repository.git
   ```

2. Install the required Python libraries:
   ```bash
   pip install selenium atlassian requests
   ```

3. Install Google Chrome if not already installed:
   - [Google Chrome](https://www.google.com/chrome/)

## Configuration

1. Create a `config.yml` file in the project directory with the following format:
   ```yaml
   username: your_confluence_username
   password: your_confluence_password
   api_url: https://your-confluence-instance-url/rest/api
   space: your_confluence_space_key
   download_path: /path/to/download/directory
   with_attachments: true
   lazy_mode: true
   web_url: https://your-confluence-instance-url
   user_data_dir: /path/to/chrome/user/data
   profile_directory: Default
   ```

2. Fill in the necessary information:
   - `username`: Your Confluence username.
   - `password`: Your Confluence password.
   - `api_url`: The URL of your Confluence API.
   - `space`: The key of the Confluence space you want to download.
   - `download_path`: The directory where downloaded pages and attachments will be saved.
   - `with_attachments`: Set to `true` if you want to download attachments along with pages.
   - `lazy_mode`: Set to `true` if you want to enable lazy mode (adds a delay between downloads).
   - `web_url`: The URL of your Confluence instance.
   - `user_data_dir`: The path to the Chrome user data directory for Selenium.
   - `profile_directory`: The Chrome profile directory for Selenium.

## Usage

Run the `confluence_downloader.py` script:
```bash
python confluence_downloader.py
```

The script will start downloading pages and attachments from the specified Confluence space according to the configuration provided in `config.yml`.
