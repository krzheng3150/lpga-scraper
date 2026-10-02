#!/usr/bin/env python3
"""LPGA Tournament Hole-by-Hole Leaderboard Scraper."""

import argparse
import time
from typing import List, Dict, Any
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def get_chrome_options() -> webdriver.ChromeOptions:
    """Configures headless Chrome options suitable for server/container environments."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument(f"user-agent={user_agent}")
    return options


def scrape_hole_by_hole_scores(url: str, tournament_title: str, round_num: int) -> None:
    """Scrapes LPGA leaderboard hole-by-hole scores for a specific round."""
    print(f"Starting scraper for tournament '{tournament_title}', Round {round_num}...")
    print(f"Target URL: {url}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=get_chrome_options(),
    )

    scraped_data: List[Dict[str, Any]] = []
    failed_indices: List[int] = []

    try:
        driver.get(url)
        print("Navigated to the leaderboard page.")

        # Wait for the main leaderboard container
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "._bg-_platformweb_1726194350"))
        )
        print("Leaderboard table detected.")

        # Wait for player rows to load completely
        player_selector = "._bg-_platformweb_1726194350 .css-175oi2r ._pl-_md_1481558369 ._columnGap-1481558369"
        player_ids = driver.find_elements(By.CSS_SELECTOR, player_selector)
        prev_count = len(player_ids)

        while True:
            player_ids = driver.find_elements(By.CSS_SELECTOR, player_selector)
            if len(player_ids) == prev_count and prev_count > 0:
                break
            prev_count = len(player_ids)
            time.sleep(2)

        print(f"Total players identified: {len(player_ids)}")

        for i, player_elem in enumerate(player_ids):
            try:
                player_name = player_elem.get_attribute("innerHTML") or f"Player_{i+1}"
                print(f"[{i+1}/{len(player_ids)}] Scraping: {player_name}")

                # Open the player detail dialog
                driver.execute_script("arguments[0].click();", player_elem)

                # Wait for dialog and round tabs
                dialog_selector = ".is_DialogContent"
                tab_selector = f"{dialog_selector} ._pl-_md_1481558245 ._btc-0hover-1394778429"
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, dialog_selector)))
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, tab_selector)))
                time.sleep(1)

                round_tabs = driver.find_elements(By.CSS_SELECTOR, tab_selector)
                if len(round_tabs) < round_num:
                    print(f"Warning: Round {round_num} tab not found for {player_name}. Skipping.")
                    continue

                driver.execute_script("arguments[0].click();", round_tabs[round_num - 1])

                # Wait for score columns
                score_col_selector = f"{dialog_selector} .css-175oi2r ._jc-_lg_441309761 ._col-_md_196791179"
                hole_col_selector = f"{dialog_selector} ._bg-_platformweb_1726194350 ._jc-_lg_441309761 ._col-_md_1561457603"

                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, score_col_selector)))
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, hole_col_selector)))

                hole_scores_elements = driver.find_elements(By.CSS_SELECTOR, score_col_selector)
                hole_scores_raw = [score.get_attribute("innerHTML") or "" for score in hole_scores_elements]

                hole_numbers_elements = driver.find_elements(By.CSS_SELECTOR, hole_col_selector)
                hole_numbers_raw = [number.get_attribute("innerHTML") or "" for number in hole_numbers_elements]

                # Locate marker column for the second nine
                split_idx = 25
                for idx in range(1, len(hole_scores_raw)):
                    if hole_scores_raw[idx].startswith("R"):
                        split_idx = idx + 1
                        break

                started_on_back_nine = len(hole_numbers_raw) > 1 and hole_numbers_raw[1] == "10"

                front_nine = hole_scores_raw[1:10]
                back_nine = hole_scores_raw[split_idx : split_idx + 9]

                ordered_scores = (back_nine + front_nine) if started_on_back_nine else (front_nine + back_nine)

                record: Dict[str, Any] = {"player": player_name}
                for hole_idx, score in enumerate(ordered_scores, start=1):
                    record[f"Hole_{hole_idx}"] = score
                scraped_data.append(record)

            except Exception as exc:
                print(f"Failed scraping player at index {i}: {exc}")
                failed_indices.append(i)

        if failed_indices:
            print(f"Encountered errors for indices: {failed_indices}")

    finally:
        driver.quit()
        print("WebDriver session closed.")

    if scraped_data:
        df = pd.DataFrame(scraped_data)
        output_file = f"lpga_scores_{tournament_title}_R{round_num}.csv"
        df.to_csv(output_file, index=False)
        print(f"Successfully saved {len(df)} records to '{output_file}'.")
    else:
        print("No records scraped. CSV was not generated.")


def parse_args() -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Scrape hole-by-hole scores from an LPGA tournament leaderboard.")
    parser.add_argument(
        "url",
        type=str,
        help="Leaderboard URL (e.g. https://www.lpga.com/tournaments/cpkc-womens-open/leaderboard)",
    )
    parser.add_argument(
        "title",
        type=str,
        help="Tournament identifier string for file naming (e.g. cpkc_open)",
    )
    parser.add_argument(
        "round_num",
        type=int,
        choices=[1, 2, 3, 4],
        help="Tournament round number (1, 2, 3, or 4)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    scrape_hole_by_hole_scores(
        url=args.url,
        tournament_title=args.title,
        round_num=args.round_num,
    )