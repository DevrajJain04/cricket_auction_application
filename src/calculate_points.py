import csv
from datetime import datetime

class FantasyPointsCalculator:
    def __init__(self):
        self.point_rules = {
            # Batting points
            'run': 1,
            'boundary_bonus': 1,
            'six_bonus': 2,
            '30_run_bonus': 4,
            'half_century_bonus': 8,
            'century_bonus': 16,
            'duck': -2,
            
            # Bowling points
            'wicket': 25,
            'stumped_bonus':6,
            'lbw_bowled_bonus': 8,
            '3_wicket_bonus': 4,
            '4_wicket_bonus': 8,
            '5_wicket_bonus': 16,
            'maiden_over': 12,
            
            # Fielding points
            'catch': 8,
            '3_catch_bonus': 4,
            'stumping': 12,
            'run_out_direct': 12,
            'run_out_indirect': 6,
            
            # Strike rate points
            'strike_rate': [
                (170, float('inf'), 6),
                (150.01, 170, 4),
                (130, 150, 2),
                (60, 70, -2),
                (50, 59.99, -4),
                (0, 50, -6)
            ],
            
            # Economy rate points
            'economy_rate': [
                (0, 5, 6),
                (5, 5.99, 4),
                (6, 7, 2),
                (10, 11, -2),
                (11.01, 12, -4),
                (12, float('inf'), -6)
            ]
        }

    def calculate_batting_points(self, player):
        points = 0
        runs = int(player.get('runs', 0))
        balls_faced = int(player.get('balls_faced', 0))
        
        points += runs * self.point_rules['run']
        points += int(player.get('fours', 0)) * self.point_rules['boundary_bonus']
        points += int(player.get('sixes', 0)) * self.point_rules['six_bonus']
        
        if runs >= 100:
            points += self.point_rules['century_bonus']
        elif runs >= 50:
            points += self.point_rules['half_century_bonus']
        elif runs >= 30:
            points += self.point_rules['30_run_bonus']
        
        if runs == 0 and int(player.get('dismissals', 0)) > 0:
            points += self.point_rules['duck']
        
        if balls_faced >= 10:
            sr = float(player.get('strike_rate', 0))
            for low, high, sr_points in self.point_rules['strike_rate']:
                if low <= sr <= high:
                    points += sr_points
                    break
        
        return points

    def calculate_bowling_points(self, player):
        points = 0
        wickets = int(player.get('wickets', 0))
        overs_bowled = float(player.get('overs_bowled', 0))
        
        
        if wickets >= 5:
            points += self.point_rules['5_wicket_bonus']
        elif wickets >= 4:
            points += self.point_rules['4_wicket_bonus']
        elif wickets >= 3:
            points += self.point_rules['3_wicket_bonus']
        
        points += int(player.get('maidens', 0)) * self.point_rules['maiden_over']
        
        if overs_bowled >= 2:
            economy = float(player.get('economy', 0))
            for low, high, eco_points in self.point_rules['economy_rate']:
                if low <= economy <= high:
                    points += eco_points
                    break
        
        return points

    def calculate_fielding_points(self, player):
        points = 0
        catches = int(player.get('catches', 0))
        
        points += catches * self.point_rules['catch']
        if catches >= 3:
            points += self.point_rules['3_catch_bonus']
        
        points += int(player.get('stumpings', 0)) * self.point_rules['stumping']
        points += int(player.get('run_outs', 0)) * self.point_rules['run_out_indirect']
        
        return points

    def is_playing_xi(self,player_data):
        """Determine if player was in original playing XI"""
        # Player definitely in XI if they batted or bowled
        if int(player_data.get('batting_innings', 0)) > 0:
            return True
        if int(player_data.get('bowling_innings', 0)) > 0:
            return True
        
        # Player might be substitute if only fielding stats exist
        if (int(player_data.get('catches', 0)) > 0 or
            int(player_data.get('stumpings', 0)) > 0 or
            int(player_data.get('run_outs', 0)) > 0):
            return False  # Likely substitute
        
        return False  # Not in playing XI

    def calculate_total_points(self, player):
        # if player was in the playing XI, calculate points
        # and if the player was just a substitute i.e. he did not bowl or bat return only fielding points and for all others add 4 points to total points
        if self.is_playing_xi(player):
            points = 4 + self.calculate_batting_points(player) + self.calculate_bowling_points(player) + self.calculate_fielding_points(player)
        else:
            points = self.calculate_fielding_points(player)

        return {
            'player_name': player.get('player_name', ''),
            'team': player.get('team', ''),
            'match_id': player.get('match_id', ''),
            'total_points': points,
            'batting_points': self.calculate_batting_points(player),
            'bowling_points': self.calculate_bowling_points(player),
            'fielding_points': self.calculate_fielding_points(player)
        }

def process_input_file(input_file):
    with open(input_file, mode='r', encoding='utf-8') as csvfile:
        return list(csv.DictReader(csvfile))

def save_output_file(players_points, output_file):
    fieldnames = ['player_name', 'team', 'match_id', 
                 'total_points', 'batting_points', 
                 'bowling_points', 'fielding_points']
    
    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(players_points)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"player_points_summary_{timestamp}.csv"
    
    calculator = FantasyPointsCalculator()
    players = process_input_file("new_test.csv")
    
    players_points = [calculator.calculate_total_points(p) for p in players]
    
    save_output_file(players_points, output_file)
    print(f"Points summary saved to {output_file}")

if __name__ == "__main__":
    main()