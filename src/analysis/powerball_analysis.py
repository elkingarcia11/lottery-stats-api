import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import os
import random
from src.analysis.lottery_analysis import LotteryAnalysis, FrequencyStats

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'raw')

class PowerballAnalyzer:
    def __init__(self, csv_file: str):
        """Initialize the PowerballAnalyzer with the CSV file path."""
        self.df = pd.read_csv(os.path.join(DATA_DIR, csv_file))
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

    def get_position_frequencies(self, position: int) -> Dict[int, float]:
        """Get frequency distribution for a specific position (0-4 for main numbers) as percentages."""
        frequencies = dict(self.position_frequencies[position])
        total = sum(frequencies.values())
        return {num: (freq / total * 100) for num, freq in frequencies.items()}

    def get_powerball_frequencies(self) -> Dict[int, float]:
        """Get frequency distribution for Powerball numbers as percentages."""
        frequencies = dict(self.powerball_frequencies)
        total = sum(frequencies.values())
        return {num: (freq / total * 100) for num, freq in frequencies.items()}

    def get_general_frequencies(self) -> Dict[int, float]:
        """Get overall frequency distribution of main numbers (excluding Powerball) as percentages."""
        frequencies = dict(self.general_frequencies)
        total = sum(frequencies.values())
        return {num: (freq / total * 100) for num, freq in frequencies.items()}

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
        total_draws = len(self.df)
        for combo, freq in self.get_repeated_combinations().items():
            main_numbers = combo[:5]
            powerball = combo[5]
            repeated_data.append({
                'Main_Numbers': ' '.join(map(str, sorted(main_numbers))),
                'Powerball': powerball,
                'Frequency': freq,
                'Percentage': (freq / total_draws * 100)
            })
        pd.DataFrame(repeated_data).sort_values(by=['Main_Numbers', 'Powerball']).to_csv(f"{output_dir}/powerball_repeated_combinations.csv", index=False)
        
        # Export position frequencies
        position_data = []
        for pos in range(5):  # Only main numbers positions
            frequencies = self.get_position_frequencies(pos)
            for number, percentage in sorted(frequencies.items()):
                position_data.append({
                    'Position': pos + 1,
                    'Number': number,
                    'Percentage': percentage
                })
        pd.DataFrame(position_data).sort_values(by=['Position', 'Number']).to_csv(f"{output_dir}/powerball_position_frequencies.csv", index=False)
        
        # Export Powerball frequencies
        powerball_data = []
        powerball_frequencies = self.get_powerball_frequencies()
        for number, percentage in sorted(powerball_frequencies.items()):
            powerball_data.append({
                'Powerball': number,
                'Percentage': percentage
            })
        pd.DataFrame(powerball_data).sort_values(by=['Powerball']).to_csv(f"{output_dir}/powerball_specific_frequencies.csv", index=False)
        
        # Export general frequencies
        general_data = []
        general_frequencies = self.get_general_frequencies()
        for number, percentage in sorted(general_frequencies.items()):
            general_data.append({
                'Number': number,
                'Percentage': percentage
            })
        pd.DataFrame(general_data).sort_values(by=['Number']).to_csv(f"{output_dir}/powerball_general_frequencies.csv", index=False)
        
        # Export optimized data
        optimized_df = self.optimize_dataframe()
        # Sort by date in descending order (most recent first)
        optimized_df['Draw_Date'] = pd.to_datetime(optimized_df['Draw_Date'])
        optimized_df = optimized_df.sort_values(by='Draw_Date', ascending=False)
        optimized_df.to_csv(f"{output_dir}/powerball_optimized_data.csv", index=False)

    def generate_unique_combination(self) -> Dict:
        """
        Generate a random combination that has never appeared in historical data.
        
        For Powerball:
        - Main numbers: 1-69
        - Powerball number: 1-26
        - Numbers must be unique for main numbers
        
        Returns:
            Dictionary containing the generated combination
        """
        max_attempts = 1000  # Prevent infinite loop
        attempts = 0
        
        while attempts < max_attempts:
            # Generate 5 unique main numbers between 1-69
            main_numbers = sorted(random.sample(range(1, 70), 5))
            # Generate Powerball number between 1-26
            powerball = random.randint(1, 26)
            
            # Check if this combination exists
            result = self.check_combination(main_numbers + [powerball])
            if not result["exists"]:
                return {
                    "main_numbers": main_numbers,
                    "powerball": powerball,
                    "attempts_needed": attempts + 1
                }
            
            attempts += 1
        
        return {"error": f"Could not find unique combination after {max_attempts} attempts"}

    def get_latest_numbers(self, limit: int = 100) -> List[Dict]:
        """
        Get the latest winning numbers with their dates.
        
        Args:
            limit: Number of recent results to return (default 100)
            
        Returns:
            List of dictionaries containing dates and winning numbers
        """
        # Convert Draw Date to datetime for proper sorting
        self.df['Draw Date'] = pd.to_datetime(self.df['Draw Date'])
        
        # Sort by date in descending order and get the latest entries
        latest_draws = self.df.sort_values('Draw Date', ascending=False).head(limit)
        
        # Convert back to string format for JSON serialization
        latest_draws['Draw Date'] = latest_draws['Draw Date'].dt.strftime('%Y-%m-%d')
        
        results = []
        for _, row in latest_draws.iterrows():
            numbers = [int(num) for num in row['Winning Numbers'].split()]
            results.append({
                'draw_date': row['Draw Date'],
                'main_numbers': numbers[:5],
                'powerball': numbers[5],
                'multiplier': row['Multiplier']
            })
        
        return results

class PowerballAnalysis(LotteryAnalysis):
    def __init__(self, csv_file: str = 'powerball.csv'):
        """Initialize the analysis with the CSV file path."""
        super().__init__(csv_file)
        self.special_ball_column = 'Powerball Ball'
        
        # Initialize analysis
        self._analysis = None
        self.special_ball_range = (1, 26)  # Powerball range
        self.main_numbers_range = (1, 69)  # Main numbers range

    def get_analysis(self) -> Dict:
        """Get comprehensive Powerball analysis."""
        stats = self.get_summary_statistics(self.special_ball_column)
        
        # Add Powerball specific statistics
        stats.update({
            'lottery_type': 'Powerball',
            'main_number_range': (1, 69),
            'special_ball_range': (1, 26),
            'coverage_statistics': self.calculate_coverage_statistics()
        })
        
        return stats
    
    def calculate_coverage_statistics(self) -> Dict:
        """Calculate how much of the possible number space has been used."""
        # Analyze main numbers coverage
        used_numbers = set()
        for numbers in self.df['number_list']:
            used_numbers.update(numbers)
        
        main_numbers_coverage = (len(used_numbers) / 69) * 100
        
        # Analyze Powerball coverage
        used_powerballs = set(self.df[self.special_ball_column].astype(int))
        powerball_coverage = (len(used_powerballs) / 26) * 100
        
        return {
            'main_numbers_coverage': main_numbers_coverage,
            'powerball_coverage': powerball_coverage,
            'unused_main_numbers': sorted(set(range(1, 70)) - used_numbers),
            'unused_powerballs': sorted(set(range(1, 27)) - used_powerballs)
        }

def main():
    # Initialize analyzer
    analyzer = PowerballAnalyzer('powerball.csv')
    
    # Generate and check a unique combination
    print("\nGenerating a unique combination that has never occurred...")
    unique_combo = analyzer.generate_unique_combination()
    if "error" not in unique_combo:
        print(f"Found unique combination after {unique_combo['attempts_needed']} attempts:")
        print(f"Main numbers: {unique_combo['main_numbers']}")
        print(f"Powerball: {unique_combo['powerball']}")
    else:
        print(unique_combo["error"])
    
    # Export all analysis results
    analyzer.export_analysis()
    print("\nAnalysis complete! Results have been exported to the 'analysis_results' directory.")

if __name__ == "__main__":
    main() 