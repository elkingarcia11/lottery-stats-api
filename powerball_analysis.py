import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import os

class PowerballAnalyzer:
    def __init__(self, csv_file: str):
        """Initialize the PowerballAnalyzer with the CSV file path."""
        self.df = pd.read_csv(csv_file)
        self.position_frequencies = defaultdict(Counter)
        self.general_frequencies = Counter()
        self.powerball_frequencies = Counter()  # New counter for Powerball numbers
        self.combination_frequencies = Counter()
        self.process_data()

    def process_data(self):
        """Process the data and calculate all frequencies."""
        for _, row in self.df.iterrows():
            # Split the winning numbers string into a list of numbers
            numbers = [int(num) for num in row['Winning Numbers'].split()]
            main_numbers = numbers[:5]  # First 5 numbers
            powerball = numbers[5]      # Last number is Powerball
            
            # Track combination frequencies
            self.combination_frequencies[tuple(numbers)] += 1
            
            # Track position frequencies for main numbers
            for pos, num in enumerate(main_numbers):
                self.position_frequencies[pos][num] += 1
                
            # Track Powerball frequencies separately
            self.powerball_frequencies[powerball] += 1
                
            # Track general frequencies (excluding Powerball)
            self.general_frequencies.update(main_numbers)

    def check_combination(self, numbers: List[int]) -> Dict:
        """
        Check if a combination exists in historical data.
        
        Args:
            numbers: List of 6 integers where first 5 are main numbers and last is Powerball
            
        Returns:
            Dictionary containing existence info and frequency if found
        """
        if len(numbers) != 6:
            return {"error": "Invalid combination. Must provide 6 numbers (5 main numbers + Powerball)"}
        
        combo_tuple = tuple(numbers)
        frequency = self.combination_frequencies.get(combo_tuple, 0)
        
        if frequency > 0:
            # Find the dates this combination occurred
            dates = []
            for _, row in self.df.iterrows():
                row_numbers = [int(num) for num in row['Winning Numbers'].split()]
                if tuple(row_numbers) == combo_tuple:
                    dates.append(row['Draw Date'])
            
            return {
                "exists": True,
                "frequency": frequency,
                "dates": dates,
                "main_numbers": numbers[:5],
                "powerball": numbers[5]
            }
        else:
            return {
                "exists": False,
                "main_numbers": numbers[:5],
                "powerball": numbers[5]
            }

    def get_repeated_combinations(self, min_occurrences: int = 2) -> Dict[Tuple[int, ...], int]:
        """Return combinations that appeared more than once."""
        return {combo: freq for combo, freq in self.combination_frequencies.items() 
                if freq >= min_occurrences}

    def get_position_frequencies(self, position: int) -> Dict[int, int]:
        """Get frequency distribution for a specific position (0-4 for main numbers)."""
        return dict(self.position_frequencies[position])

    def get_powerball_frequencies(self) -> Dict[int, int]:
        """Get frequency distribution for Powerball numbers."""
        return dict(self.powerball_frequencies)

    def get_general_frequencies(self) -> Dict[int, int]:
        """Get overall frequency distribution of main numbers (excluding Powerball)."""
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
                'Powerball': numbers[5],
                'Multiplier': row['Multiplier'],
                'Original_Combination': row['Winning Numbers']
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
            main_numbers = combo[:5]
            powerball = combo[5]
            repeated_data.append({
                'Main_Numbers': ' '.join(map(str, main_numbers)),
                'Powerball': powerball,
                'Frequency': freq
            })
        pd.DataFrame(repeated_data).to_csv(f"{output_dir}/powerball_repeated_combinations.csv", index=False)
        
        # Export position frequencies
        position_data = []
        for pos in range(5):  # Only main numbers positions
            frequencies = self.get_position_frequencies(pos)
            for number, freq in frequencies.items():
                position_data.append({
                    'Position': pos + 1,
                    'Number': number,
                    'Frequency': freq
                })
        pd.DataFrame(position_data).to_csv(f"{output_dir}/powerball_position_frequencies.csv", index=False)
        
        # Export Powerball frequencies
        powerball_data = []
        for number, freq in self.get_powerball_frequencies().items():
            powerball_data.append({
                'Powerball': number,
                'Frequency': freq
            })
        pd.DataFrame(powerball_data).to_csv(f"{output_dir}/powerball_specific_frequencies.csv", index=False)
        
        # Export general frequencies
        general_data = []
        for number, freq in self.get_general_frequencies().items():
            general_data.append({
                'Number': number,
                'Frequency': freq
            })
        pd.DataFrame(general_data).to_csv(f"{output_dir}/powerball_general_frequencies.csv", index=False)
        
        # Export optimized data
        self.optimize_dataframe().to_csv(f"{output_dir}/powerball_optimized_data.csv", index=False)

def main():
    # Initialize analyzer
    analyzer = PowerballAnalyzer('powerball.csv')
    
    # Example of checking a combination
    print("\nChecking example combination...")
    example_combination = [1, 2, 3, 4, 5, 6]  # Example numbers
    result = analyzer.check_combination(example_combination)
    if result.get("exists"):
        print(f"Combination found!")
        print(f"Occurred {result['frequency']} times")
        print(f"Draw dates: {', '.join(result['dates'])}")
    else:
        print("Combination has never occurred in historical data")
    
    # Export all analysis results
    analyzer.export_analysis()
    print("\nAnalysis complete! Results have been exported to the 'analysis_results' directory.")

if __name__ == "__main__":
    main() 