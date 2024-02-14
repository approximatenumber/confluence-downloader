# Confluence Snapshot

Confluence Snaphost is a Python application designed to download Confluence space pages as PDF files including attachments. This tool may be useful if you don't have access to PDF API or other page export and automation API (it may be disabled by Confluence admin).

Main features:

 * pages are downloaded as PDF files using `selenium`
 * attachments are downloaded separately using Confluence REST API

Downloaded page tree example:

```
IPH
├── IPhone
│   ├── IPhone13
│   │   ├── Specification.attachments
│   │   │   ├── pic1.png
│   │   │   ├── pic2.png
│   │   │   └── pic3.png
│   │   └── Specification.pdf
│   ├── IPhone13.pdf
│   ├── IPhone14
│   │   ├── Prices.attachments
│   │   │   └── prices.xlsx
│   │   ├── Prices.pdf
│   │   ├── Specification.attachments
│   │   │   └── pic1.png
│   │   └── Specification.pdf
│   └── IPhone14.pdf
└── IPhone.pdf
```

## Requirements

- Python 3.8+
- external dependencies from `requirements.txt`
- Google Chrome and webdriver (for `selenium`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/your-repository.git
   ```

2. Install the required Python libraries:
   ```bash
   pip install -r requirements
   ```

3. Install Google Chrome and ChromeWebdriver if not already installed:
   - [Google Chrome](https://www.google.com/chrome/)
   - [Webdriver](https://chromedriver.chromium.org/downloads)

## Configuration

1. Fill `config.yml` file in the project directory with the following format:
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
