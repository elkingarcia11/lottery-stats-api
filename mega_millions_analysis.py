import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

class MegaMillionsAnalyzer:
    def __init__(self, csv_file: str):
        """Initialize the MegaMillionsAnalyzer with the CSV file path."""
        self.df = pd.read_csv(csv_file)
        self.position_frequencies = defaultdict(Counter)
        self.general_frequencies = Counter()
        self.megaball_frequencies = Counter()
        self.combination_frequencies = Counter()
        self.process_data()

    def process_data(self):
        """Process the data and calculate all frequencies."""
        for _, row in self.df.iterrows():
            # Split the winning numbers string into a list of numbers
            numbers = [int(num) for num in row['Winning Numbers'].split()]
            megaball = int(row['Mega Ball'])
            
            # Create full combination including Mega Ball
            full_combination = tuple(numbers + [megaball])
            
            # Track combination frequencies
            self.combination_frequencies[full_combination] += 1
            
            # Track position frequencies for main numbers
            for pos, num in enumerate(numbers):
                self.position_frequencies[pos][num] += 1
                
            # Track Mega Ball frequencies separately
            self.megaball_frequencies[megaball] += 1
                
            # Track general frequencies (excluding Mega Ball)
            self.general_frequencies.update(numbers)

    def get_repeated_combinations(self, min_occurrences: int = 2) -> Dict[Tuple[int, ...], int]:
        """Return combinations that appeared more than once."""
        return {combo: freq for combo, freq in self.combination_frequencies.items() 
                if freq >= min_occurrences}

    def get_position_frequencies(self, position: int) -> Dict[int, int]:
        """Get frequency distribution for a specific position (0-4 for main numbers)."""
        return dict(self.position_frequencies[position])

    def get_megaball_frequencies(self) -> Dict[int, int]:
        """Get frequency distribution for Mega Ball numbers."""
        return dict(self.megaball_frequencies)

    def get_general_frequencies(self) -> Dict[int, int]:
        """Get overall frequency distribution of main numbers."""
        return dict(self.general_frequencies)

    def optimize_dataframe(self) -> pd.DataFrame:
        """Create an optimized DataFrame with separate columns for each number."""
        optimized_data = []
        
        for _, row in self.df.iterrows():
            numbers = [int(num) for num in row['Winning Numbers'].split()]
            entry = {
                'Draw_Date': row['Draw Date'],
                'Number_1': numbers[0],
                'Number_2': numbers[1],
                'Number_3': numbers[2],
                'Number_4': numbers[3],
                'Number_5': numbers[4],
                'Mega_Ball': int(row['Mega Ball']),
                'Multiplier': row['Multiplier'],
                'Original_Combination': f"{row['Winning Numbers']} MB:{row['Mega Ball']}"
            }
            optimized_data.append(entry)
            
        return pd.DataFrame(optimized_data)

def main():
    # Initialize analyzer
    analyzer = MegaMillionsAnalyzer('mega_million.csv')
    
    # Get and print repeated combinations
    print("\nRepeated Combinations (appeared more than once):")
    repeated = analyzer.get_repeated_combinations()
    for combo, freq in repeated.items():
        main_numbers = combo[:-1]
        mega_ball = combo[-1]
        print(f"Combination {main_numbers} MB:{mega_ball}: appeared {freq} times")
    
    # Print position frequencies
    print("\nPosition-wise Frequencies:")
    for pos in range(5):  # Mega Millions has 5 main numbers
        print(f"\nPosition {pos + 1}:")
        frequencies = analyzer.get_position_frequencies(pos)
        sorted_freq = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
        for number, freq in sorted_freq[:5]:  # Show top 5 numbers for each position
            print(f"Number {number}: {freq} times")
    
    # Print Mega Ball frequencies
    print("\nMega Ball Frequencies (Top 10):")
    mega_freq = analyzer.get_megaball_frequencies()
    sorted_mega = sorted(mega_freq.items(), key=lambda x: x[1], reverse=True)
    for number, freq in sorted_mega[:10]:
        print(f"Mega Ball {number}: {freq} times")
    
    # Print overall frequencies
    print("\nOverall Number Frequencies (Top 10, excluding Mega Ball):")
    general_freq = analyzer.get_general_frequencies()
    sorted_general = sorted(general_freq.items(), key=lambda x: x[1], reverse=True)
    for number, freq in sorted_general[:10]:
        print(f"Number {number}: {freq} times")
    
    # Create optimized DataFrame
    print("\nCreating optimized DataFrame...")
    optimized_df = analyzer.optimize_dataframe()
    print("Sample of optimized data:")
    print(optimized_df.head())

if __name__ == "__main__":
    main() 