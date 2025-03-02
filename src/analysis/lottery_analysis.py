import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Set
import numpy as np
from dataclasses import dataclass
import os

# Constants
DATA_DIR = 'data/raw'

@dataclass
class FrequencyStats:
    count: int
    percentage: float

class LotteryAnalysis:
    def __init__(self, csv_file: str):
        """Initialize the analysis with a CSV file containing lottery data."""
        self.df = pd.read_csv(os.path.join(DATA_DIR, csv_file))
        self.total_draws = len(self.df)
        
        # Convert winning numbers from space-separated string to list of integers
        self.df['number_list'] = self.df['Winning Numbers'].apply(lambda x: [int(n) for n in str(x).split()])
        
        # Calculate total numbers drawn (5 numbers per draw)
        self.total_numbers = self.total_draws * 5
    
    def analyze_overall_frequencies(self) -> Dict[int, FrequencyStats]:
        """Analyze frequency of each number appearing in any position."""
        all_numbers = []
        for numbers in self.df['number_list']:
            all_numbers.extend(numbers)
            
        counter = Counter(all_numbers)
        frequencies = {}
        
        for number, count in counter.items():
            frequencies[number] = FrequencyStats(
                count=count,
                percentage=(count / self.total_numbers) * 100
            )
            
        return frequencies
    
    def analyze_position_frequencies(self) -> Dict[int, Dict[int, FrequencyStats]]:
        """Analyze frequency of each number appearing in each specific position."""
        position_numbers = defaultdict(list)
        
        # Collect numbers by position
        for numbers in self.df['number_list']:
            for pos, num in enumerate(numbers, 1):
                position_numbers[pos].append(num)
        
        position_frequencies = {}
        for position in range(1, 6):
            counter = Counter(position_numbers[position])
            frequencies = {}
            
            for number, count in counter.items():
                frequencies[number] = FrequencyStats(
                    count=count,
                    percentage=(count / self.total_draws) * 100
                )
                
            position_frequencies[position] = frequencies
            
        return position_frequencies
    
    def analyze_special_ball_frequencies(self, special_ball_column: str) -> Dict[int, FrequencyStats]:
        """Analyze frequency of each special ball number."""
        counter = Counter(self.df[special_ball_column])
        frequencies = {}
        
        for number, count in counter.items():
            frequencies[int(number)] = FrequencyStats(
                count=count,
                percentage=(count / self.total_draws) * 100
            )
            
        return frequencies
    
    def analyze_number_combination_frequencies(self) -> Dict[Tuple[int, ...], FrequencyStats]:
        """Analyze frequency of winning number combinations (without special ball)."""
        combinations = [tuple(sorted(nums)) for nums in self.df['number_list']]
        counter = Counter(combinations)
        frequencies = {}
        
        for combination, count in counter.items():
            frequencies[combination] = FrequencyStats(
                count=count,
                percentage=(count / self.total_draws) * 100
            )
            
        return frequencies
    
    def analyze_full_combination_frequencies(self, special_ball_column: str) -> Dict[Tuple[int, ...], FrequencyStats]:
        """Analyze frequency of complete winning combinations (including special ball)."""
        full_combinations = []
        for _, row in self.df.iterrows():
            numbers = tuple(sorted(row['number_list']) + [int(row[special_ball_column])])
            full_combinations.append(numbers)
            
        counter = Counter(full_combinations)
        frequencies = {}
        
        for combination, count in counter.items():
            frequencies[combination] = FrequencyStats(
                count=count,
                percentage=(count / self.total_draws) * 100
            )
            
        return frequencies
    
    def get_summary_statistics(self, special_ball_column: str) -> Dict:
        """Get comprehensive summary of all analyses."""
        return {
            'total_draws': self.total_draws,
            'overall_frequencies': self.analyze_overall_frequencies(),
            'position_frequencies': self.analyze_position_frequencies(),
            'special_ball_frequencies': self.analyze_special_ball_frequencies(special_ball_column),
            'number_combination_frequencies': self.analyze_number_combination_frequencies(),
            'full_combination_frequencies': self.analyze_full_combination_frequencies(special_ball_column)
        } 