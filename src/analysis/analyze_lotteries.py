import pandas as pd
from src.analysis.mega_millions_analysis import MegaMillionsAnalysis
from src.analysis.powerball_analysis import PowerballAnalysis
from datetime import datetime
import os

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
ANALYSIS_DIR = os.path.join(DATA_DIR, 'analysis')

def format_frequency_data(freq_dict, lottery_type, category):
    """Convert frequency dictionary to DataFrame rows."""
    rows = []
    for number, stats in freq_dict.items():
        rows.append({
            'Lottery': lottery_type,
            'Category': category,
            'Number': number,
            'Count': stats.count,
            'Percentage': stats.percentage
        })
    return rows

def format_position_data(pos_freq_dict, lottery_type):
    """Convert position frequency dictionary to DataFrame rows."""
    rows = []
    for position, numbers in pos_freq_dict.items():
        for number, stats in numbers.items():
            rows.append({
                'Lottery': lottery_type,
                'Position': position,
                'Number': number,
                'Count': stats.count,
                'Percentage': stats.percentage
            })
    return rows

def format_combination_data(combo_freq_dict, lottery_type, category):
    """Convert combination frequency dictionary to DataFrame rows."""
    rows = []
    for combo, stats in combo_freq_dict.items():
        rows.append({
            'Lottery': lottery_type,
            'Category': category,
            'Combination': ' '.join(map(str, combo)),
            'Count': stats.count,
            'Percentage': stats.percentage
        })
    return rows

def analyze_and_export():
    """Run analyses for both lotteries and export results to CSV files."""
    # Create analysis directory if it doesn't exist
    os.makedirs(ANALYSIS_DIR, exist_ok=True)

    # Initialize analyzers
    mega = MegaMillionsAnalysis()
    power = PowerballAnalysis()
    
    # Get analyses
    mega_analysis = mega.get_analysis()
    power_analysis = power.get_analysis()

    # 1. Overall Statistics
    stats_rows = []
    for lottery, analysis in [('Mega Millions', mega_analysis), ('Powerball', power_analysis)]:
        stats_rows.append({
            'Lottery': lottery,
            'Total Draws': analysis['total_draws'],
            'Main Numbers Range': f"{analysis['main_number_range'][0]}-{analysis['main_number_range'][1]}",
            'Special Ball Range': f"{analysis['special_ball_range'][0]}-{analysis['special_ball_range'][1]}",
            'Main Numbers Coverage (%)': analysis['coverage_statistics']['main_numbers_coverage'],
            'Special Ball Coverage (%)': analysis['coverage_statistics']['mega_ball_coverage' if lottery == 'Mega Millions' else 'powerball_coverage']
        })
    pd.DataFrame(stats_rows).to_csv(os.path.join(ANALYSIS_DIR, 'overall_statistics.csv'), index=False)

    # 2. Number Frequencies
    frequency_rows = []
    # Mega Millions frequencies
    frequency_rows.extend(format_frequency_data(mega_analysis['overall_frequencies'], 'Mega Millions', 'Main Numbers'))
    frequency_rows.extend(format_frequency_data(mega_analysis['special_ball_frequencies'], 'Mega Millions', 'Mega Ball'))
    # Powerball frequencies
    frequency_rows.extend(format_frequency_data(power_analysis['overall_frequencies'], 'Powerball', 'Main Numbers'))
    frequency_rows.extend(format_frequency_data(power_analysis['special_ball_frequencies'], 'Powerball', 'Powerball'))
    
    pd.DataFrame(frequency_rows).to_csv(os.path.join(ANALYSIS_DIR, 'number_frequencies.csv'), index=False)

    # 3. Position-specific Frequencies
    position_rows = []
    position_rows.extend(format_position_data(mega_analysis['position_frequencies'], 'Mega Millions'))
    position_rows.extend(format_position_data(power_analysis['position_frequencies'], 'Powerball'))
    
    pd.DataFrame(position_rows).to_csv(os.path.join(ANALYSIS_DIR, 'position_frequencies.csv'), index=False)

    # 4. Combination Frequencies
    combination_rows = []
    # Main number combinations (without special ball)
    combination_rows.extend(format_combination_data(mega_analysis['number_combination_frequencies'], 'Mega Millions', 'Main Numbers Only'))
    combination_rows.extend(format_combination_data(power_analysis['number_combination_frequencies'], 'Powerball', 'Main Numbers Only'))
    # Full combinations (with special ball)
    combination_rows.extend(format_combination_data(mega_analysis['full_combination_frequencies'], 'Mega Millions', 'Full Combination'))
    combination_rows.extend(format_combination_data(power_analysis['full_combination_frequencies'], 'Powerball', 'Full Combination'))
    
    pd.DataFrame(combination_rows).to_csv(os.path.join(ANALYSIS_DIR, 'combination_frequencies.csv'), index=False)

    # 5. Unused Numbers Report
    unused_rows = []
    for lottery, analysis in [('Mega Millions', mega_analysis), ('Powerball', power_analysis)]:
        coverage = analysis['coverage_statistics']
        unused_rows.append({
            'Lottery': lottery,
            'Category': 'Main Numbers',
            'Unused Numbers': ', '.join(map(str, coverage['unused_main_numbers']))
        })
        unused_rows.append({
            'Lottery': lottery,
            'Category': 'Special Ball',
            'Unused Numbers': ', '.join(map(str, coverage['unused_mega_balls' if lottery == 'Mega Millions' else 'unused_powerballs']))
        })
    
    pd.DataFrame(unused_rows).to_csv(os.path.join(ANALYSIS_DIR, 'unused_numbers.csv'), index=False)

    print("\nAnalysis complete! Results have been exported to the 'analysis' directory.")
    print("\nFiles created:")
    print("1. overall_statistics.csv - General statistics for both lotteries")
    print("2. number_frequencies.csv - Frequency analysis of all numbers")
    print("3. position_frequencies.csv - Position-specific number frequencies")
    print("4. combination_frequencies.csv - Analysis of winning combinations")
    print("5. unused_numbers.csv - Numbers that have never been drawn")

if __name__ == "__main__":
    analyze_and_export() 