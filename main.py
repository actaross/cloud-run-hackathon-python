
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

previous_score = 0
score_stagnant_count = 0
consecutive_hits_count = 0
player_url = ""
player_x = 0
player_y = 0
player_direction = ""
player_score = 0
player_hit = False
opponents = []


def set_player_position(x, y):
    global player_x, player_y
    player_x = x
    player_y = y

def set_player_direction(direction):
    global player_direction
    player_direction = direction

def set_player_score(score):
    global player_score
    player_score = score

def set_player_hit_status(hit):
    global player_hit
    player_hit = hit

    
def set_player_and_opponents(data):
    global player_url, opponents
    player_url = None
    service_url = data['_links']['self']['href']
    # Extract player URL and opponent data from the received data
    for url, player_data in data['arena']['state'].items():
        if url.endswith(service_url):
            player_url = url
            set_player_position(player_data['x'], player_data['y'])
            set_player_direction(player_data['direction'])
            set_player_score(player_data['score'])
            set_player_hit_status(player_data['wasHit'])
        else:
            opponent = {
                'url': url,
                'position': (player_data['x'], player_data['y']),
                'direction': player_data['direction'],
                'score': player_data['score'],
                'wasHit': player_data['wasHit']
            }
            opponents.append(opponent)
    
    return player_url, opponents

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
    global player_score, previous_score, score_stagnant_count, consecutive_hits_count
    #Original
    request.get_data()
    player_url, opponents = set_player_and_opponents(request.json)
    # Check if score is increasing
    print("Player Information:")
    print(f"Position: ({player_x}, {player_y})")
    print(f"Direction: {player_direction}")
    print(f"Hit: {player_hit}")
    print(f"Score: {player_score}")
    
    if player_score > previous_score:
        previous_score = player_score
        score_stagnant_count = 0
        return 'T'
    else:
        previous_score= player_score
    print(f"Score: {player_score}")
    print(f"previous_score: {previous_score}")
    print(f"consecutive_hits_count: {consecutive_hits_count}")
    if player_hit:
        consecutive_hits_count += 1
        if consecutive_hits_count >= 2:
            last_hit_direction = get_opponent_direction(player_x, player_y, opponents)
            if last_hit_direction != player_direction:
                if last_hit_direction == 'N':
                    return 'R'
                elif last_hit_direction == 'S':
                    return 'L'
                else:
                    return 'F'
    # Reset consecutive hits count if not hit in the current turn
    else:
        consecutive_hits_count = 0
    # Check if any opponent is in front and within range distance 3
    if is_any_opponent_in_front(player_x, player_y, player_direction, opponents):
        return 'T'
    return moves[random.randrange(len(moves))]

if __name__ == "__main__":
  app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))


