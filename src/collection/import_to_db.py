#!/usr/bin/env python3
import sqlite3
import pandas as pd
import os
from pathlib import Path

# Constants
DATA_DIR = Path(__file__).parent.parent.parent / 'data' / 'raw'
ANALYSIS_DIR = Path(__file__).parent.parent.parent / 'data' / 'analysis'
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'lottery.db'

def create_database():
    """Create the SQLite database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the draws table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS draws (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lottery_type TEXT NOT NULL,
        draw_date DATE NOT NULL,
        winning_numbers TEXT NOT NULL,
        special_ball INTEGER NOT NULL,
        multiplier INTEGER NOT NULL DEFAULT 1
    )
    ''')
    
    # Create indices
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_draw_date ON draws (draw_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_winning_numbers ON draws (winning_numbers)')
    
    # Create frequency tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS position_frequencies (
        lottery_type TEXT NOT NULL,
        position INTEGER NOT NULL,
        number INTEGER NOT NULL,
        frequency INTEGER NOT NULL,
        percentage REAL NOT NULL,
        PRIMARY KEY (lottery_type, position, number)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS number_frequencies (
        lottery_type TEXT NOT NULL,
        number INTEGER NOT NULL,
        frequency INTEGER NOT NULL,
        percentage REAL NOT NULL,
        PRIMARY KEY (lottery_type, number)
    )
    ''')
    
    conn.commit()
    return conn

def import_csv_to_db(csv_path: Path, lottery_type: str, conn: sqlite3.Connection):
    """Import data from CSV file into the database."""
    print(f"Importing {lottery_type} data from {csv_path}")
    
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Convert data to the format we need
    records = []
    
    # Define column names based on lottery type
    if lottery_type == 'mega_millions':
        special_ball_column = 'Mega Ball'
    else:  # powerball
        special_ball_column = 'Powerball Ball'
    
    for _, row in df.iterrows():
        # Convert draw date to ISO format for SQLite
        draw_date = pd.to_datetime(row['Draw Date']).strftime('%Y-%m-%d')
        
        # Convert multiplier to int, default to 1 if not present or invalid
        try:
            multiplier = int(row.get('Multiplier', 1))
        except (ValueError, TypeError):
            multiplier = 1
        
        records.append((
            lottery_type,
            draw_date,
            row['Winning Numbers'],
            int(row[special_ball_column]),
            multiplier
        ))
    
    # Insert records in batches
    cursor = conn.cursor()
    cursor.executemany(
        'INSERT INTO draws (lottery_type, draw_date, winning_numbers, special_ball, multiplier) VALUES (?, ?, ?, ?, ?)',
        records
    )
    conn.commit()
    print(f"Imported {len(records)} records for {lottery_type}")

def import_frequencies(conn: sqlite3.Connection):
    """Import frequency data from analysis CSVs."""
    cursor = conn.cursor()
    
    # Clear existing frequency data
    cursor.execute('DELETE FROM position_frequencies')
    cursor.execute('DELETE FROM number_frequencies')
    
    # Import position frequencies
    position_file = ANALYSIS_DIR / 'position_frequencies.csv'
    if position_file.exists():
        print("\nImporting position frequencies...")
        df = pd.read_csv(position_file)
        
        position_records = []
        for _, row in df.iterrows():
            # Convert lottery name to match our format
            lottery_type = row['Lottery'].lower().replace(' ', '_')
            
            position_records.append((
                lottery_type,
                row['Position'],
                row['Number'],
                row['Count'],
                row['Percentage']
            ))
        
        cursor.executemany(
            'INSERT INTO position_frequencies (lottery_type, position, number, frequency, percentage) VALUES (?, ?, ?, ?, ?)',
            position_records
        )
        print(f"Imported {len(position_records)} position frequency records")
    
    # Import number frequencies
    number_file = ANALYSIS_DIR / 'number_frequencies.csv'
    if number_file.exists():
        print("\nImporting number frequencies...")
        df = pd.read_csv(number_file)
        
        number_records = []
        for _, row in df.iterrows():
            # Convert lottery name to match our format
            lottery_type = row['Lottery'].lower().replace(' ', '_')
            
            if row['Category'] == 'Main Numbers':  # Only import main number frequencies
                number_records.append((
                    lottery_type,
                    row['Number'],
                    row['Count'],
                    row['Percentage']
                ))
        
        cursor.executemany(
            'INSERT INTO number_frequencies (lottery_type, number, frequency, percentage) VALUES (?, ?, ?, ?)',
            number_records
        )
        print(f"Imported {len(number_records)} number frequency records")
    
    conn.commit()

def main():
    # Create database and tables
    conn = create_database()
    
    try:
        # Import draw data
        powerball_csv = DATA_DIR / 'powerball.csv'
        if powerball_csv.exists():
            import_csv_to_db(powerball_csv, 'powerball', conn)
        else:
            print(f"Warning: {powerball_csv} not found")
        
        mega_millions_csv = DATA_DIR / 'mega_millions.csv'
        if mega_millions_csv.exists():
            import_csv_to_db(mega_millions_csv, 'mega_millions', conn)
        else:
            print(f"Warning: {mega_millions_csv} not found")
        
        # Import frequency data
        import_frequencies(conn)
        
        # Print summary
        cursor = conn.cursor()
        print("\nDatabase Summary:")
        print("-----------------")
        
        cursor.execute('SELECT lottery_type, COUNT(*) FROM draws GROUP BY lottery_type')
        for lottery_type, count in cursor.fetchall():
            print(f"Total {lottery_type} draws: {count}")
        
        cursor.execute('SELECT lottery_type, COUNT(*) FROM position_frequencies GROUP BY lottery_type')
        for lottery_type, count in cursor.fetchall():
            print(f"Total {lottery_type} position frequencies: {count}")
        
        cursor.execute('SELECT lottery_type, COUNT(*) FROM number_frequencies GROUP BY lottery_type')
        for lottery_type, count in cursor.fetchall():
            print(f"Total {lottery_type} number frequencies: {count}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main() 