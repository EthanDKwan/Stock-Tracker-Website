# Stock Tracker

A web application for tracking stock prices and generating buy/sell signals using historical and real-time data.

## Features
- **Real-time stock price tracking**: Monitor live stock prices.
- **Buy/sell signal generation**: Based on technical indicators (e.g., SMA, MACD).
- **Interactive graphs**: Visualize data using Plotly.
- **Notifications**: Get alerts for buy/sell signals (coming soon).

## Technologies Used
- **Frontend**: HTML, CSS, JavaScript, Plotly
- **Backend**: Python, Flask
- **APIs**: yfinance, AlphaVantage API

## Installation
1. Clone the repository: 
- git clone https://github.com/your-username/stock-tracker.git)

Install dependencies: 
- pip install -r requirements.txt

Run the Flask app:
- python app.py
Open your browser and navigate to http://localhost:5000.


Usage
Enter a stock ticker (e.g., AAPL) to view historical data and buy/sell signals.

Real-time updates and notifications are available in the live version.

About the Project
Problem Statement
The casual stock trader/investor often does not continuously monitor stock movements or incorporate short-term price changes (e.g., due to news, financial reports, or patents). Instead, they may buy a market-conglomerate ETF and adopt a "set-and-forget" strategy. While effective, this raises the question: Can a more informed trading strategy be implemented to help while requiring minimal attention, knowledge, and time?

Concept
This project explores a semi-automated, rule-based trading algorithm that:

Runs continuously in the background.

Notifies users of potential trading opportunities based on pre-defined strategies.

Minimizes attention, time, and knowledge requirements while aiming to outperform the market.

Note: This goal is a challenge even for multi-trillion-dollar financial industries. While I don’t expect to solve it entirely, I hope to learn and build something interesting along the way.

Author
Ethan D. Kwan
This project was conceived and developed starting February 2nd, 2025, as a platform to practice trading knowledge and software development skills.

## License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

Looking forward to the journey on this project!

Ethan :]