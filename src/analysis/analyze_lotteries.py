#!/usr/bin/env python3
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'lottery.db'

def calculate_frequencies(conn: sqlite3.Connection, lottery_type: str):
    """Calculate number frequencies and position frequencies for a lottery type."""
    cursor = conn.cursor()
    
    # Enable dictionary access for rows
    cursor.row_factory = sqlite3.Row
    
    # Get total number of draws
    cursor.execute(
        'SELECT COUNT(*) as count FROM draws WHERE lottery_type = ?',
        (lottery_type,)
    )
    total_draws = cursor.fetchone()['count']
    
    if total_draws == 0:
        logger.warning(f"No draws found for {lottery_type}")
        return
    
    logger.info(f"Analyzing {total_draws} draws for {lottery_type}")
    
    # Clear existing frequency data for this lottery type
    cursor.execute('DELETE FROM number_frequencies WHERE lottery_type = ?', (lottery_type,))
    cursor.execute('DELETE FROM position_frequencies WHERE lottery_type = ?', (lottery_type,))
    
    # Get all draws
    cursor.execute(
        'SELECT winning_numbers, special_ball FROM draws WHERE lottery_type = ?',
        (lottery_type,)
    )
    
    # Initialize counters
    number_counts = Counter()
    position_counts = defaultdict(Counter)
    
    # Process each draw
    for row in cursor.fetchall():
        main_numbers = [int(n) for n in row['winning_numbers'].split()]
        special_ball = row['special_ball']
        
        # Count overall number frequencies
        number_counts.update(main_numbers)
        
        # Count position-specific frequencies
        for pos, num in enumerate(main_numbers, 1):
            position_counts[pos][num] += 1
        
        # Count special ball frequencies
        position_counts[6][special_ball] += 1
    
    # Insert overall number frequencies
    number_records = []
    for number, count in number_counts.items():
        percentage = (count / (total_draws * 5)) * 100  # 5 numbers per draw
        number_records.append((lottery_type, number, count, percentage))
    
    cursor.executemany('''
        INSERT INTO number_frequencies (lottery_type, number, frequency, percentage)
        VALUES (?, ?, ?, ?)
    ''', number_records)
    
    # Insert position-specific frequencies
    position_records = []
    for position, counts in position_counts.items():
        for number, count in counts.items():
            percentage = (count / total_draws) * 100
            position_records.append((lottery_type, position, number, count, percentage))
    
    cursor.executemany('''
        INSERT INTO position_frequencies (lottery_type, position, number, frequency, percentage)
        VALUES (?, ?, ?, ?, ?)
    ''', position_records)
    
    conn.commit()
    logger.info(f"Updated {len(number_records)} number frequencies and {len(position_records)} position frequencies")

def analyze_and_export():
    """Analyze lottery data and update frequency tables."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # Enable dictionary access for rows
        conn.row_factory = sqlite3.Row
        
        # Ensure frequency tables exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS number_frequencies (
                lottery_type TEXT,
                number INTEGER,
                frequency INTEGER,
                percentage REAL,
                PRIMARY KEY (lottery_type, number)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS position_frequencies (
                lottery_type TEXT,
                position INTEGER,
                number INTEGER,
                frequency INTEGER,
                percentage REAL,
                PRIMARY KEY (lottery_type, position, number)
            )
        ''')
        
        # Analyze each lottery type
        for lottery_type in ['powerball', 'mega-millions']:
            logger.info(f"\nAnalyzing {lottery_type}...")
            calculate_frequencies(conn, lottery_type)
        
        logger.info("\nAnalysis complete!")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        conn.rollback()
        raise
        
    finally:
        conn.close()

if __name__ == '__main__':
    analyze_and_export() 