#!/usr/bin/env python

import argparse
import ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import time


def fetch_historical_data(exchange_id, symbol, timeframe, start_date=None, end_date=None, page_limit=200):
    """
    Fetches available historical data by paginating through multiple requests.
    Handles BitMart's pagination (~200 rows per request).

    BitMart pagination behavior:
    - Returns data in chronological order (oldest first)
    - Typically returns ~200 candles per request
    - Use the last timestamp from each batch + 1 timeframe unit as 'since' for next batch

    :param exchange_id: The ID of the exchange (e.g., 'bitmart').
    :param symbol: The trading pair (e.g., 'KAG/USDT').
    :param timeframe: Intraday timeframe (e.g., '1h').
    :param start_date: Start date as datetime object (optional, fetches from earliest available if None).
    :param end_date: End date as datetime object (defaults to today if None).
    :param page_limit: Number of candles per request (BitMart typically returns ~200).
    :return: A pandas DataFrame with all historical OHLCV data.
    """
    exchange = getattr(ccxt, exchange_id)({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    # Set end_date to now minus 1 hour if not provided
    if end_date is None:
        end_date = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)

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
            current_since = last_timestamp + _timeframe_delta_ms(timeframe)

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


def _timeframe_delta_ms(timeframe):
    """Return one timeframe in milliseconds."""
    if timeframe == '1h':
        return 60 * 60 * 1000
    if timeframe == '1d':
        return 24 * 60 * 60 * 1000
    if timeframe.endswith('m'):
        return int(timeframe.rstrip('m')) * 60 * 1000
    return 60 * 60 * 1000  # default 1h


def _read_existing_csv(csv_path):
    """
    Read existing CSV; supports simple format (datetime, open, high, low, close, volume)
    and CryptoDataDownload format (unix, date, symbol, open, high, low, close, Volume X, Volume Y).
    Returns (df_with_datetime_index, is_cryptodatadownload_format, volume_col_name).
    """
    df = pd.read_csv(csv_path)
    # CryptoDataDownload format has 'unix', 'date', 'symbol'
    if 'unix' in df.columns and 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])
        df.set_index('datetime', inplace=True)
        # Find volume column (Volume BASE)
        vol_cols = [c for c in df.columns if c.startswith('Volume ')]
        vol_col = vol_cols[0] if vol_cols else None
        return df, True, vol_col
    # Simple format: first column is usually datetime index
    if df.columns[0] in ('datetime', 'date', 'Unnamed: 0'):
        idx_col = 0
        df = pd.read_csv(csv_path, index_col=idx_col, parse_dates=True)
    else:
        df = pd.read_csv(csv_path, parse_dates=True)
        if 'datetime' in df.columns:
            df.set_index('datetime', inplace=True)
    # Simple format uses 'volume' column
    return df, False, 'volume'


def expand_csv(csv_path, exchange_id, symbol, timeframe, page_limit=200, end_date=None):
    """
    Continue a data download from an existing CSV: take the last timestamp,
    add one timeframe, and download up until end_date (default: today) or out of data.
    Merges new data with existing and overwrites the file.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    existing_df, is_cdd_format, vol_col = _read_existing_csv(csv_path)

    # Last timestamp (as datetime for display)
    last_dt = existing_df.index.max()
    if hasattr(last_dt, 'to_pydatetime'):
        last_dt = last_dt.to_pydatetime()
    if hasattr(last_dt, 'tzinfo') and last_dt.tzinfo is not None:
        last_dt = last_dt.replace(tzinfo=None)

    # Start from last_ts + one timeframe
    delta_ms = _timeframe_delta_ms(timeframe)
    if 'unix' in existing_df.columns:
        # CryptoDataDownload format: unix can be in seconds or milliseconds
        last_ms = int(existing_df['unix'].max())
        if last_ms < 1e12:  # likely seconds (e.g. 1.6e9)
            last_ms *= 1000
        start_ms = last_ms + delta_ms
        start_date = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc).replace(tzinfo=None)
    else:
        # Simple format (datetime index): add one timeframe directly — avoid ns/ms confusion
        start_date = last_dt + timedelta(milliseconds=delta_ms)

    if end_date is None:
        end_date = datetime.now().replace(minute=0, second=0, microsecond=0)

    print(f"Expand: last row in CSV is {last_dt}")
    print(f"Expand: fetching from {start_date} until {end_date}")

    new_df = fetch_historical_data(
        exchange_id, symbol, timeframe,
        start_date=start_date,
        end_date=end_date,
        page_limit=page_limit
    )

    if new_df.empty:
        print("No new data; file unchanged.")
        return existing_df

    # Normalize existing to OHLCV with 'volume'
    if is_cdd_format and vol_col:
        existing_ohlcv = existing_df[['open', 'high', 'low', 'close', vol_col]].copy()
        existing_ohlcv.rename(columns={vol_col: 'volume'}, inplace=True)
    else:
        existing_ohlcv = existing_df[['open', 'high', 'low', 'close', 'volume']].copy()

    combined = pd.concat([existing_ohlcv, new_df])
    combined = combined[~combined.index.duplicated(keep='last')]
    combined.sort_index(inplace=True)

    # Save back in same format
    if is_cdd_format:
        save_to_cryptodatadownload_format(combined, symbol, csv_path)
    else:
        combined.to_csv(csv_path)

    print(f"Expand: merged {len(new_df)} new rows; total {len(combined)} rows. Saved to {csv_path}")
    return combined


def save_to_cryptodatadownload_format(df, symbol, output_file):
    """
    Saves DataFrame to CSV format similar to CryptoDataDownload.com.
    df must have columns open, high, low, close, volume and a datetime index.
    """
    df_out = df.reset_index()
    df_out.rename(columns={'index': 'datetime'}, inplace=True)
    df_out['unix'] = (df_out['datetime'].astype('int64') // 10**6).astype(int)
    df_out['date'] = df_out['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_out['symbol'] = symbol
    base, quote = symbol.split('/')[0], symbol.split('/')[1]
    df_out.rename(columns={'volume': f'Volume {base}'}, inplace=True)
    df_out[f'Volume {quote}'] = (df_out['close'] * df_out[f'Volume {base}']).round(4)
    cols = ['unix', 'date', 'symbol', 'open', 'high', 'low', 'close', f'Volume {base}', f'Volume {quote}']
    df_out[cols].to_csv(output_file, index=False)


def _parse_date(s):
    """Parse ISO date string (YYYY-MM-DD) to naive datetime at midnight."""
    if s is None:
        return None
    dt = datetime.fromisoformat(s.strip())
    return dt.replace(hour=0, minute=0, second=0, microsecond=0) if dt else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch OHLCV data from an exchange via ccxt (e.g. BitMart KAG/USDT).",
    )
    parser.add_argument(
        "--expand",
        metavar="FILE",
        help="Continue download: read last timestamp from FILE, add one timeframe, "
             "download until --end or today, merge and overwrite FILE.",
    )
    parser.add_argument(
        "--exchange",
        default="bitmart",
        help="Exchange id (default: bitmart).",
    )
    parser.add_argument(
        "--symbol",
        default="KAG/USDT",
        help="Trading pair (default: KAG/USDT).",
    )
    parser.add_argument(
        "--timeframe",
        default="1h",
        help="Candle timeframe: 1m, 5m, 15m, 1h, 1d (default: 1h).",
    )
    parser.add_argument(
        "--page-limit",
        type=int,
        default=200,
        metavar="N",
        help="Candles per request (default: 200).",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Output CSV path (default: ./csv/Exchange_SYMBOL_TIMEFRAME.csv).",
    )
    parser.add_argument(
        "--start",
        metavar="YYYY-MM-DD",
        help="Start date for full download (default: earliest available).",
    )
    parser.add_argument(
        "--end",
        metavar="YYYY-MM-DD",
        help="End date (default: today).",
    )
    args = parser.parse_args()

    exchange_id = args.exchange
    symbol = args.symbol
    timeframe = args.timeframe
    page_limit = args.page_limit
    output_file = args.output or f"./csv/{exchange_id.capitalize()}_{symbol.replace('/', '_')}_{timeframe}.csv"
    start_date = _parse_date(args.start)
    end_date = _parse_date(args.end)

    if args.expand:
        expand_csv(
            args.expand,
            exchange_id,
            symbol,
            timeframe,
            page_limit=page_limit,
            end_date=end_date,
        )
    else:
        if end_date is None:
            end_date = datetime.now().replace(minute=0, second=0, microsecond=0)

        print(f"Downloading historical {symbol} {timeframe} data from {exchange_id}...")
        print(f"Using page limit: {page_limit} candles per request\n")

        data = fetch_historical_data(
            exchange_id,
            symbol,
            timeframe,
            start_date=start_date,
            end_date=end_date,
            page_limit=page_limit,
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

            data.to_csv(output_file)
            print(f"Saved to {output_file}")
        else:
            print("\nFailed to download data.")
