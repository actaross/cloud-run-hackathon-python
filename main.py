
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

service_url = None
player_url = None
player_x = None
player_y = None
player_direction = None
player_score = None
was_hit = None
previous_score = None
score_stagnant_count = 0
consecutive_hits_count = 0

def set_player_and_opponents(data):
    global player_url, player_x, player_y, player_direction, player_score, was_hit, previous_score
    global score_stagnant_count, consecutive_hits_count

    arena_data = data['arena']
    player_data = None
    opponents_data = []

    # Find player's data based on self href URL
    for url, info in arena_data['state'].items():
        if info['_links']['self']['href'] == player_url:
            player_data = info
        else:
            opponents_data.append(info)

    # Set player's attributes
    player_x = player_data['x']
    player_y = player_data['y']
    player_direction = player_data['direction']
    player_score = player_data['score']
    was_hit = player_data['wasHit']
    previous_score = player_score

    # Reset counts
    score_stagnant_count = 0
    consecutive_hits_count = 0

    return opponents_data

def calculate_distance(x1, y1, x2, y2):
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

def calculate_threat_level(opponent, player_x, player_y):
    opp_x, opp_y = opponent['x'], opponent['y']
    distance = calculate_distance(player_x, player_y, opp_x, opp_y)
    return 1 / distance

def get_opponent_direction(player_x, player_y, opponents):
    for opponent in opponents:
        opp_x, opp_y = opponent['x'], opponent['y']
        if calculate_distance(player_x, player_y, opp_x, opp_y) <= 3:
            return opponent['direction']

    return random.choice(['N', 'S', 'W', 'E'])

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
        opp_x, opp_y = opponent['x'], opponent['y']
        if (opp_x - player_x) * dx >= 0 and (opp_y - player_y) * dy >= 0:
            if calculate_distance(player_x, player_y, opp_x, opp_y) <= range_distance:
                return True

    return False

@app.route("/", methods=['GET'])
def index():
    return "Let the battle begin!"

@app.route("/", methods=['POST'])
def move():
    #Original
    #request.get_data()
global player_score, previous_score, score_stagnant_count, consecutive_hits_count

    opponents_data = set_player_and_opponents(request.json)

    if player_score > previous_score:
        previous_score = player_score
        score_stagnant_count = 0

    if was_hit:
        consecutive_hits_count += 1
        if consecutive_hits_count >= 2:
            last_hit_direction = get_opponent_direction(player_x, player_y, opponents_data)
            if last_hit_direction != player_direction:
                if last_hit_direction == 'N':
                    return 'R'
                elif last_hit_direction == 'S':
                    return 'L'
                else:
                    return 'T'

 
    # Original
    return moves[random.randrange(len(moves))]

if __name__ == "__main__":
  app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
  
