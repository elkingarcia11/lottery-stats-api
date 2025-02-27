import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import os

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

    def export_analysis(self, output_dir: str = "analysis_results"):
        """Export all analysis results to CSV files."""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Export repeated combinations
        repeated_data = []
        for combo, freq in self.get_repeated_combinations().items():
            main_numbers = combo[:-1]
            mega_ball = combo[-1]
            repeated_data.append({
                'Main_Numbers': ' '.join(map(str, main_numbers)),
                'Mega_Ball': mega_ball,
                'Frequency': freq
            })
        pd.DataFrame(repeated_data).to_csv(f"{output_dir}/mega_millions_repeated_combinations.csv", index=False)
        
        # Export position frequencies
        position_data = []
        for pos in range(5):
            frequencies = self.get_position_frequencies(pos)
            for number, freq in frequencies.items():
                position_data.append({
                    'Position': pos + 1,
                    'Number': number,
                    'Frequency': freq
                })
        pd.DataFrame(position_data).to_csv(f"{output_dir}/mega_millions_position_frequencies.csv", index=False)
        
        # Export Mega Ball frequencies
        mega_data = []
        for number, freq in self.get_megaball_frequencies().items():
            mega_data.append({
                'Mega_Ball': number,
                'Frequency': freq
            })
        pd.DataFrame(mega_data).to_csv(f"{output_dir}/mega_millions_megaball_frequencies.csv", index=False)
        
        # Export general frequencies
        general_data = []
        for number, freq in self.get_general_frequencies().items():
            general_data.append({
                'Number': number,
                'Frequency': freq
            })
        pd.DataFrame(general_data).to_csv(f"{output_dir}/mega_millions_general_frequencies.csv", index=False)
        
        # Export optimized data
        self.optimize_dataframe().to_csv(f"{output_dir}/mega_millions_optimized_data.csv", index=False)

def main():
    # Initialize analyzer
    analyzer = MegaMillionsAnalyzer('mega_million.csv')
    
    # Export all analysis results
    analyzer.export_analysis()
    print("Analysis complete! Results have been exported to the 'analysis_results' directory.")

if __name__ == "__main__":
    main() 