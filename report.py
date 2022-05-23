import yfinance as yf
import pandas as pd


sp500 = yf.Ticker("^GSPC")
end_date = pd.Timestamp.today()
start_date = end_date - pd.Timedelta(days=10*365)
sp500_history=sp500.history(start=start_date, end=end_date)


sp500_history = sp500_history.drop(columns=['Dividends', 'Stock Splits'])

sp500_history['Close_200ma'] = sp500_history['Close'].rolling(200).mean()


sp500_history_summary = sp500_history.describe()