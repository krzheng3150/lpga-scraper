# LPGA Hole-by-Hole Leaderboard Scraper

A Python and Selenium-based automation tool that extracts hole-by-hole scores for each golfer from an LPGA tournament leaderboard and outputs the results to a CSV file.

## Prerequisites

### System Dependencies (Debian/Ubuntu)
Headless Chrome requires system-level GUI dependencies and Google Chrome installed:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates fonts-liberation libappindicator3-1 libasound2 \
    libatk-bridge2.0-0 libnspr4 libnss3 lsb-release xdg-utils wget

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/lpga-scraper.git
   cd lpga-scraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the scraper by passing the tournament leaderboard URL, a tournament tag for the output filename, and the round number (1-4):

```bash
python lpga_scraper.py <url> <tournament_title> <round_number>
```

### Example

```bash
python lpga_scraper.py \
  "https://www.lpga.com/tournaments/cpkc-womens-open/leaderboard" \
  "cpkc_womens_open" \
  1
```

This generates `lpga_scores_cpkc_womens_open_R1.csv` containing player names and their corresponding scores for holes 1 through 18.

## License
MIT