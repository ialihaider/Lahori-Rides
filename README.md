# PakWheels Car Scraper

A Python script that scrapes car listings from PakWheels.com and sends notifications via Slack when matching cars are found.

## Features

- Searches for specific car models:
  - Suzuki Cultus (2017-2019)
  - Suzuki Swift DLX 1.3
- Filters by location (Lahore)
- Sends notifications via Slack when matching cars are found
- Runs on a schedule (every 30 minutes)
- Prevents duplicate notifications

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pakwheels-scraper.git
   cd pakwheels-scraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Slack credentials:
   ```
   SLACK_TOKEN=your-slack-bot-token
   SLACK_CHANNEL=your-channel-id
   ```

5. Run the scraper:
   ```bash
   python pakwheels_scraper.py
   ```

## Configuration

- Edit `pakwheels_scraper.py` to modify:
  - Search criteria (car models, years, location)
  - Price limits
  - Notification settings

## Files

- `pakwheels_scraper.py` - Main scraper script
- `test_scraper.py` - Test script for debugging
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (not tracked in git)
- `.gitignore` - Git ignore rules

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
