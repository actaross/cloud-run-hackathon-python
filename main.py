
# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import random
from flask import Flask, request, jsonify


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)
moves = ['F', 'T', 'L', 'R']

previous_move = 'F'
previous_score = 0
consecutive_hits_count = 0
score_stagnant_count = 0

# Helper function to calculate Euclidean distance between two points
def calculate_distance(x1, y1, x2, y2):
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

# Helper function to calculate threat level of an opponent
def calculate_threat_level(opponent, player_x, player_y):
    opp_x, opp_y = opponent['position']
    distance = calculate_distance(player_x, player_y, opp_x, opp_y)
    return 1 / distance

# Helper function to get the direction of the opponent
def get_opponent_direction(player_x, player_y, opponents):
    for opponent in opponents:
        opp_x, opp_y = opponent['position']
        if calculate_distance(player_x, player_y, opp_x, opp_y) <= 3:
            return opponent['direction']

    # Default to a random direction if unable to determine the opponent's direction
    return random.choice(['N', 'S', 'W', 'E'])

# Helper function to check if any opponent is in front and within range distance 3
def is_any_opponent_in_front(player_x, player_y, player_direction, opponents):
    directions = {
        'N': (0, -1),
        'S': (0, 1),
        'W': (-1, 0),
        'E': (1, 0)
    }
    range_distance = 3

    dx, dy = directions[player_direction]
    for opponent in opponents:
        opp_x, opp_y = opponent['position']
        if (opp_x - player_x) * dx >= 0 and (opp_y - player_y) * dy >= 0:
            if calculate_distance(player_x, player_y, opp_x, opp_y) <= range_distance:
                return True

    return False

def set_player_and_opponent(arena_state):
    player = None
    opponents = []

    for player_url, player_info in arena_state['arena']['state'].items():
        if player_url == service_url:
            player = {
                'x': player_info['x'],
                'y': player_info['y'],
                'direction': player_info['direction'],
                'wasHit': player_info['wasHit'],
                'score': player_info['score']
            }
        else:
            opponent = {
                'x': player_info['x'],
                'y': player_info['y'],
                'direction': player_info['direction'],
                'wasHit': player_info['wasHit'],
                'score': player_info['score']
            }
            opponents.append(opponent)

    return player, opponents

@app.route("/", methods=['GET'])
def index():
    return "Let the battle begin!"

@app.route("/", methods=['POST'])
def move():
    #Original
    #request.get_data()
 global previous_move, previous_score, consecutive_hits_count, score_stagnant_count

    # Log the received message
    logger.info(request.json)

    # Get the current arena state from the request
    arena_state = request.json

    # Set player and opponent based on the arena state
    player, opponents = set_player_and_opponent(arena_state)

    # Extract player information
    player_x = player['x']
    player_y = player['y']
    player_direction = player['direction']
    was_hit = player['wasHit']
    player_score = player['score']

    # Check if score is increasing
    if player_score > previous_score:
        previous_score = player_score
        score_stagnant_count = 0

    # Check if consecutive hits occurred and move to escape
    if was_hit:
        consecutive_hits_count += 1
        if consecutive_hits_count >= 2:
            # Get the last hit direction
            last_hit_direction = get_opponent_direction(player_x, player_y, opponents)

            # Move to escape based on the last hit direction
            if last_hit_direction != player_direction:
                return jsonify({'move': last_hit_direction})
            else:
                move = random.choices(['L', 'R'], weights=[0.7, 0.3])[0]
                return jsonify({'move': move})

    # Reset consecutive hits count if not hit in the current turn
    if not was_hit:
        consecutive_hits_count = 0

    # Check if any opponent is in front and within range distance 3
    if is_any_opponent_in_front(player_x, player_y, player_direction, opponents):
        previous_move = 'T'
        return jsonify({'move': 'T'})

    # Check if score has not changed for 5 consecutive turns
    if player_score == previous_score and score_stagnant_count <= 4:
        score_stagnant_count += 1
        previous_move = random.choices(['F', 'R'], weights=[0.7, 0.3])[0]
        return jsonify({'move': previous_move})

    # Calculate threat levels for all opponents
    threat_levels = []
    for opponent in opponents:
        threat_level = calculate_threat_level(opponent, player_x, player_y)
        threat_levels.append((opponent, threat_level))

    # Sort opponents by threat level in descending order
    sorted_opponents = sorted(threat_levels, key=lambda x: x[1], reverse=True)

    # Target opponent with highest threat level
    target_opponent = sorted_opponents[0][0]

    # Determine the direction to the target opponent based on player's direction
    target_x, target_y = target_opponent['position']
    if player_direction == 'N':
        if target_y < player_y:
            return jsonify({'move': 'F'})
        elif target_y > player_y:
            move = random.choices(['L', 'R'], weights=[0.7, 0.3])[0]
            return jsonify({'move': move})
    elif player_direction == 'S':
        if target_y < player_y:
            move = random.choices(['L', 'R'], weights=[0.7, 0.3])[0]
            return jsonify({'move': move})
        elif target_y > player_y:
            return jsonify({'move': 'F'})
    elif player_direction == 'W':
        if target_x < player_x:
            return jsonify({'move': 'F'})
        elif target_x > player_x:
            move = random.choices(['L', 'R'], weights=[0.7, 0.3])[0]
            return jsonify({'move': move})
    elif player_direction == 'E':
        if target_x < player_x:
            move = random.choices(['L', 'R'], weights=[0.7, 0.3])[0]
            return jsonify({'move': move})
        elif target_x > player_x:
            return jsonify({'move': 'F'})

    # If no specific conditions are met, move forward ('F') by default
    return jsonify({'move': 'F'})
    
    
    
    # Original
    # return moves[random.randrange(len(moves))]

if __name__ == "__main__":
  app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
  
