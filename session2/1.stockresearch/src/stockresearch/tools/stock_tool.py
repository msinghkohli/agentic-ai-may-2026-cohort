from typing import Type

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GetStockPriceInput(BaseModel):
    """Input schema for GetStockPriceTool."""

    ticker: str = Field(
        ..., description="The stock ticker symbol (e.g., 'GOOGL', 'AAPL')."
    )
    start_date: str = Field(
        ..., description="Start date for historical data in YYYY-MM-DD format."
    )
    end_date: str = Field(
        ..., description="End date for historical data in YYYY-MM-DD format."
    )


class GetStockPriceTool(BaseTool):
    name: str = "get_stock_price"
    description: str = "Fetches historical stock price data for a given ticker between start_date and end_date."
    args_schema: Type[BaseModel] = GetStockPriceInput

    def _run(self, ticker: str, start_date: str, end_date: str) -> str:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            if hist.empty:
                return f"No price data found for {ticker} between {start_date} and {end_date}."

            # Return a markdown string or simple string format of the dates and closing prices
            # Just taking the Close prices for simplicity to keep the string small
            result = f"Stock Price Data for {ticker} from {start_date} to {end_date}:\n"
            for date, row in hist.iterrows():
                result += f"Date: {date.strftime('%Y-%m-%d')}, Closing Price: ${row['Close']:.2f}\n"
            return result
        except Exception as e:
            return f"Error fetching stock data for {ticker}: {str(e)}"
