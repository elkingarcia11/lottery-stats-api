#!/usr/bin/env python3
import sqlite3
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

# Constants
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'lottery.db'

def get_draws_df(conn: sqlite3.Connection, lottery_type: str) -> pd.DataFrame:
    """Get draws data for a specific lottery type from the database."""
    query = "SELECT * FROM draws WHERE lottery_type = ? ORDER BY draw_date DESC"
    return pd.read_sql_query(query, conn, params=(lottery_type,))

def analyze_number_frequencies(df: pd.DataFrame, lottery_type: str) -> List[Tuple]:
    """Analyze overall number frequencies from draw data."""
    total_draws = len(df)
    number_counts = Counter()
    
    # Count occurrences of each number
    for _, row in df.iterrows():
        numbers = [int(n) for n in row['winning_numbers'].split()]
        number_counts.update(numbers)
    
    # Convert to database records
    records = []
    for number, count in number_counts.items():
        percentage = (count / (total_draws * 5)) * 100  # 5 numbers per draw
        records.append((
            lottery_type,
            number,
            count,
            percentage
        ))
    
    return records

def analyze_position_frequencies(df: pd.DataFrame, lottery_type: str) -> List[Tuple]:
    """Analyze position-specific frequencies from draw data."""
    total_draws = len(df)
    position_counts = defaultdict(Counter)
    
    # Count occurrences of each number in each position
    for _, row in df.iterrows():
        numbers = [int(n) for n in row['winning_numbers'].split()]
        for pos, num in enumerate(numbers, 1):  # 1-based position indexing
            position_counts[pos][num] += 1
        
        # Add special ball frequencies (position 6)
        position_counts[6][row['special_ball']] += 1
    
    # Convert to database records
    records = []
    for position, counts in position_counts.items():
        for number, count in counts.items():
            percentage = (count / total_draws) * 100
            records.append((
                lottery_type,
                position,
                number,
                count,
                percentage
            ))
    
    return records

def update_frequencies(conn: sqlite3.Connection):
    """Update frequency tables in the database."""
    cursor = conn.cursor()
    
    # Clear existing frequency data
    cursor.execute('DELETE FROM number_frequencies')
    cursor.execute('DELETE FROM position_frequencies')
    
    # Analyze each lottery type
    for lottery_type in ['powerball', 'mega_millions']:
        print(f"\nAnalyzing {lottery_type}...")
        
        # Get draw data
        df = get_draws_df(conn, lottery_type)
        if len(df) == 0:
            print(f"No data found for {lottery_type}")
            continue
        
        # Analyze and update number frequencies
        number_records = analyze_number_frequencies(df, lottery_type)
        cursor.executemany(
            'INSERT INTO number_frequencies (lottery_type, number, frequency, percentage) VALUES (?, ?, ?, ?)',
            number_records
        )
        print(f"Updated {len(number_records)} number frequency records")
        
        # Analyze and update position frequencies
        position_records = analyze_position_frequencies(df, lottery_type)
        cursor.executemany(
            'INSERT INTO position_frequencies (lottery_type, position, number, frequency, percentage) VALUES (?, ?, ?, ?, ?)',
            position_records
        )
        print(f"Updated {len(position_records)} position frequency records")
    
    conn.commit()

def print_summary(conn: sqlite3.Connection):
    """Print summary statistics of the analysis."""
    cursor = conn.cursor()
    
    print("\nAnalysis Summary:")
    print("----------------")
    
    # Draw counts
    cursor.execute('SELECT lottery_type, COUNT(*) FROM draws GROUP BY lottery_type')
    for lottery_type, count in cursor.fetchall():
        print(f"\n{lottery_type.upper()}:")
        print(f"Total draws analyzed: {count}")
        
        # Most frequent numbers
        cursor.execute('''
            SELECT number, frequency, percentage 
            FROM number_frequencies 
            WHERE lottery_type = ? 
            ORDER BY frequency DESC 
            LIMIT 5
        ''', (lottery_type,))
        print("\nMost frequent numbers:")
        for number, freq, pct in cursor.fetchall():
            print(f"Number {number}: {freq} times ({pct:.2f}%)")
        
        # Most frequent numbers by position
        print("\nMost frequent numbers by position:")
        for position in range(1, 7):
            pos_name = "Special Ball" if position == 6 else f"Position {position}"
            cursor.execute('''
                SELECT number, frequency, percentage 
                FROM position_frequencies 
                WHERE lottery_type = ? AND position = ? 
                ORDER BY frequency DESC 
                LIMIT 1
            ''', (lottery_type, position))
            number, freq, pct = cursor.fetchone()
            print(f"{pos_name}: {number} ({freq} times, {pct:.2f}%)")

def main():
    """Main function to run the analysis."""
    conn = sqlite3.connect(DB_PATH)
    
    try:
        print("Starting lottery analysis...")
        update_frequencies(conn)
        print_summary(conn)
        print("\nAnalysis complete!")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main() 