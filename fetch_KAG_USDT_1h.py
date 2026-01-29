#!/usr/bin/env python

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os
import time


def fetch_intraday_data(exchange_id, symbol, timeframe, since=None, limit=1000):
    """
    Fetches intraday OHLCV data from a specified exchange.

    :param exchange_id: The ID of the exchange (e.g., 'binance', 'bitmart').
    :param symbol: The trading pair (e.g., 'KAG/USDT').
    :param timeframe: Intraday timeframe (e.g., '1h', '1m', '5m', '15m').
    :param since: Unix timestamp in milliseconds for the start date (optional).
    :param limit: Number of candles to fetch per request (exchange specific, often max 500 or 1000).
    :return: A pandas DataFrame with OHLCV data.
    """
    try:
        # Instantiate the exchange
        exchange = getattr(ccxt, exchange_id)({
            'rateLimit': 1200,  # Adjust rate limit as needed
            'enableRateLimit': True,
        })

        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)

        if not ohlcv:
            print(f"No data found for {symbol} on {exchange_id}")
            return pd.DataFrame()

        # Convert to Pandas DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)

        return df

    except ccxt.ExchangeNotAvailable as e:
        print(f"Exchange not available: {e}")
    except ccxt.NetworkError as e:
        print(f"Network error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return pd.DataFrame()


def fetch_all_historical_data(exchange_id, symbol, timeframe, start_date=None, end_date=None, page_limit=200):
    """
    Fetches all available historical data by paginating through multiple requests.
    Handles BitMart's pagination (~200 rows per request).
    
    BitMart pagination behavior:
    - Returns data in chronological order (oldest first)
    - Typically returns ~200 candles per request
    - Use the last timestamp from each batch + 1 timeframe unit as 'since' for next batch
    
    :param exchange_id: The ID of the exchange (e.g., 'bitmart').
    :param symbol: The trading pair (e.g., 'KAG/USDT').
    :param timeframe: Intraday timeframe (e.g., '1h').
    :param start_date: Start date as datetime object (optional, fetches from earliest available if None).
    :param end_date: End date as datetime object (defaults to yesterday if None).
    :param page_limit: Number of candles per request (BitMart typically returns ~200).
    :return: A pandas DataFrame with all historical OHLCV data.
    """
    exchange = getattr(ccxt, exchange_id)({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })
    
    # Set end_date to now minus 1 hour if not provided
    if end_date is None:
        end_date = datetime.now().replace(minute=0, second=0, microsecond=0).timedelta(hours=1)
    
    # Convert dates to milliseconds timestamps
    end_timestamp_ms = int(end_date.timestamp() * 1000)
    since = None
    if start_date:
        since = int(start_date.timestamp() * 1000)
    
    all_data = []
    current_since = since
    page_count = 0
    
    print(f"Fetching historical data for {symbol} on {exchange_id}...")
    if start_date:
        print(f"  Start date: {start_date}")
    print(f"  End date: {end_date}")
    print(f"  Page limit: {page_limit} candles per request")
    print()
    
    while True:
        try:
            page_count += 1
            # Fetch a page
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=page_limit)
            
            if not ohlcv or len(ohlcv) == 0:
                print(f"  Page {page_count}: No data returned. Stopping.")
                break
            
            # Check if we've reached or passed the end date
            # BitMart typically returns data in chronological order (oldest first)
            # Get the last timestamp from this batch
            last_timestamp = ohlcv[-1][0]
            last_datetime = pd.to_datetime(last_timestamp, unit='ms')
            
            # Filter out any data beyond end_date
            filtered_ohlcv = [candle for candle in ohlcv if candle[0] <= end_timestamp_ms]
            
            if filtered_ohlcv:
                all_data.extend(filtered_ohlcv)
                print(f"  Page {page_count}: Fetched {len(filtered_ohlcv)} candles (last: {last_datetime}), total: {len(all_data)}")
            
            # If we got less than the page limit - 1, we've reached the end of available data
            if len(ohlcv) < page_limit - 1:
                print(f"  Page {page_count}: Received {len(ohlcv)} candles (< {page_limit}). End of data.")
                break
            
            # If the last timestamp is at or beyond end_date, stop
            if last_timestamp >= end_timestamp_ms:
                print(f"  Page {page_count}: Reached end date ({end_date}). Stopping.")
                break
            
            # Update since to the timestamp of the last candle + 1 timeframe unit
            # This ensures we don't miss any data and don't duplicate the last candle
            if timeframe == '1h':
                current_since = last_timestamp + (60 * 60 * 1000)  # Add 1 hour in milliseconds
            elif timeframe.endswith('m'):
                timeframe_minutes = int(timeframe.rstrip('m'))
                current_since = last_timestamp + (timeframe_minutes * 60 * 1000)
            elif timeframe == '1d':
                current_since = last_timestamp + (24 * 60 * 60 * 1000)  # Add 1 day
            else:
                # Default: add 1 hour
                current_since = last_timestamp + (60 * 60 * 1000)
            
            # Rate limiting - be respectful to the exchange
            time.sleep(exchange.rateLimit / 1000)
            
        except ccxt.NetworkError as e:
            print(f"  Network error on page {page_count}: {e}")
            print(f"  Retrying after 5 seconds...")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"  Error on page {page_count}: {e}")
            print(f"  Stopping. Total data fetched so far: {len(all_data)} candles")
            break
    
    if not all_data:
        print("\nNo data was fetched.")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    df.drop('timestamp', axis=1, inplace=True)
    
    # Remove duplicates and sort
    df = df[~df.index.duplicated(keep='first')]
    df.sort_index(inplace=True)
    
    # Final filter: ensure we don't exceed end_date
    df = df[df.index <= end_date]
    
    print(f"\nFetching complete!")
    print(f"  Total pages fetched: {page_count}")
    print(f"  Total candles: {len(df)}")
    if len(df) > 0:
        print(f"  Date range: {df.index.min()} to {df.index.max()}")
    
    return df


def update_existing_data(exchange_id, symbol, timeframe, existing_csv_file):
    """
    Updates an existing CSV file with new data since the last entry.
    Useful for incremental updates.
    """
    if not os.path.exists(existing_csv_file):
        print(f"File {existing_csv_file} does not exist. Fetching all data...")
        return fetch_all_historical_data(exchange_id, symbol, timeframe)
    
    # Read existing data
    existing_df = pd.read_csv(existing_csv_file)
    existing_df['datetime'] = pd.to_datetime(existing_df['date'])
    existing_df.set_index('datetime', inplace=True)
    
    # Get the last timestamp
    last_timestamp = existing_df['unix'].max()
    last_datetime = pd.to_datetime(existing_df.index.max())
    
    print(f"Last data point: {last_datetime}")
    print(f"Fetching new data since {last_datetime}...")
    
    # Fetch new data
    since_ms = int(last_datetime.timestamp() * 1000) + (60 * 60 * 1000)  # Start from next hour
    new_data = fetch_intraday_data(exchange_id, symbol, timeframe, since=since_ms, limit=10000)
    
    if new_data.empty:
        print("No new data available.")
        return existing_df
    
    # Combine and deduplicate
    # Convert existing to same format
    existing_ohlcv = existing_df[['open', 'high', 'low', 'close', 'Volume KAG']].copy()
    existing_ohlcv.rename(columns={'Volume KAG': 'volume'}, inplace=True)
    
    combined = pd.concat([existing_ohlcv, new_data])
    combined = combined[~combined.index.duplicated(keep='last')]
    combined.sort_index(inplace=True)
    
    return combined


if __name__ == "__main__":
    # --- Configuration ---
    EXCHANGE_ID = 'bitmart'
    SYMBOL = 'KAG/USDT'
    TIMEFRAME = '1h'
    PAGE_LIMIT = 200  # BitMart typically returns ~200 rows per request
    OUTPUT_FILE = f"{SYMBOL.replace('/', '_')}_{TIMEFRAME}.csv"
    
    # Optional: Set a specific start date (leave as None to fetch from earliest available)
    #START_DATE = None
    START_DATE = datetime(2025, 1, 1)
    
    # End date defaults to yesterday if not specified
    #END_DATE = None  # Will default to yesterday
    END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    
    # Option 1: Fetch all historical data (use this for initial download)
    print(f"Downloading historical {SYMBOL} {TIMEFRAME} data from {EXCHANGE_ID}...")
    print(f"Using page limit: {PAGE_LIMIT} candles per request\n")
    
    data = fetch_all_historical_data(
        EXCHANGE_ID, 
        SYMBOL, 
        TIMEFRAME,
        start_date=START_DATE,
        end_date=END_DATE,
        page_limit=PAGE_LIMIT
    )
    
    if not data.empty:
        print(f"\n{'='*60}")
        print(f"Data downloaded successfully:")
        print(f"  Total records: {len(data)}")
        print(f"  Date range: {data.index.min()} to {data.index.max()}")
        print(f"\nFirst few records:")
        print(data.head())
        print(f"\nLast few records:")
        print(data.tail())
        
        # Save in simple format
        output = f"{SYMBOL.replace('/', '_')}_{TIMEFRAME}.csv"
        data.to_csv(output)
        print(f"Saved to {output}")
    else:
        print("\nFailed to download data.")