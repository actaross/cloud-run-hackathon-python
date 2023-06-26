
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

# Global variables
player = None
opponents = []


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

def set_players_and_opponents(data):
    global players, opponents

    players_data = data['state']
    self_href = data['_links']['self']['href']

    for player_url, player_data in players_data.items():
        if player_url == self_href:
            players.append(player_data)
        else:
            opponents.append(player_data)

@app.route("/", methods=['GET'])
def index():
    return "Let the battle begin!"

@app.route("/", methods=['POST'])
def move():
    #Original
    #request.get_data()
    global player, opponents
    data = request.get_json()

    # Set player and opponents
    set_player_and_opponent(data)

    # Extract player information
    player_x = player['position'][0]
    player_y = player['position'][1]
    player_direction = player['direction']
    was_hit = player['wasHit']
    player_score = player['score']
    
    # Check if score is increasing
    if player_score > previous_score:
        previous_score = player_score
        score_stagnant_count = 0
    
    # Original
    return moves[random.randrange(len(moves))]

if __name__ == "__main__":
  app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
  
