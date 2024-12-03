# tracker.py

import hashlib
import os
import threading
import time

import requests
from bs4 import BeautifulSoup
from loguru import logger
# Refactored fetcher - 2026-03-11
# Refactored notifier - 2026-03-11
# Refactored notifier - 2026-03-11
# Refactored differ - 2026-03-11
# Refactored differ - 2026-03-11


class WebsiteTracker:
    """Monitors a list of websites for content changes."""

    def __init__(self, urls, on_change_callback, storage_dir=".tracker_storage"):
        self.urls = urls
        self.on_change_callback = on_change_callback
        self.storage_dir = storage_dir
        self.is_running = False
        self.thread = None

        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def _get_storage_path(self, url):
        """Generate a unique file path for a given URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.storage_dir, f"{url_hash}.txt")

    def _check_url(self, url):
        """Fetch a URL and compare its content to the stored version."""
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            # Extract main content to reduce noise from ads or dynamic scripts
            main_content = soup.body.get_text(separator=" ", strip=True)

            storage_path = self._get_storage_path(url)

            if os.path.exists(storage_path):
                with open(storage_path, "r", encoding="utf-8") as f:
                    last_content = f.read()

                if main_content != last_content:
                    logger.info(f"Change detected on {url}")
                    self.on_change_callback(url, main_content)
                    with open(storage_path, "w", encoding="utf-8") as f:
                        f.write(main_content)
            else:
                logger.info(f"First check for {url}. Storing initial content.")
                with open(storage_path, "w", encoding="utf-8") as f:
                    f.write(main_content)

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")

    def _run_loop(self, interval):
        """The main loop that periodically checks all URLs."""
        while self.is_running:
            for url in self.urls:
                self._check_url(url)
            time.sleep(interval)

    def start(self, interval=60):
        """Start the monitoring thread."""
        if self.is_running:
            logger.warning("Tracker is already running.")
            return

        logger.info(f"Starting tracker with a {interval}-second interval.")
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, args=(interval,), daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the monitoring thread."""
        if not self.is_running:
            logger.warning("Tracker is not running.")
            return

        logger.info("Stopping tracker...")
        self.is_running = False
        if self.thread:
            self.thread.join()
        logger.info("Tracker stopped.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor a website for changes.")
    parser.add_argument("--url", required=True, help="The URL to monitor.")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds.")
    args = parser.parse_args()

    def simple_callback(url, content):
        print(f"[CHANGE DETECTED] The content of {url} has changed.")

    tracker = WebsiteTracker(urls=[args.url], on_change_callback=simple_callback)
    tracker.start(interval=args.interval)

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        tracker.stop()
