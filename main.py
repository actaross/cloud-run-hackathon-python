
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
move_count = 0


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

def calculate_threat_level(opponent, player_x, player_y, player_direction, player_score):
    opp_x, opp_y = opponent['position']
    opp_direction = opponent['direction']
    distance = calculate_distance(player_x, player_y, opp_x, opp_y)

    # Calculate the threat level based on distance, opponent score, and position
    threat_level = 1 / distance + (opponent['score'] - player_score) / 10

    # Adjust the threat level based on opponent position and direction
    if opp_direction == player_direction:
        if opp_direction == 'N' and opp_y < player_y:
            threat_level += 0.2
        elif opp_direction == 'S' and opp_y > player_y:
            threat_level += 0.2
        elif opp_direction == 'W' and opp_x < player_x:
            threat_level += 0.2
        elif opp_direction == 'E' and opp_x > player_x:
            threat_level += 0.2
    #Adjust the threat level based on score difference with the highest scoring opponent
    score_difference = opponent['score'] - player_score
    if score_difference > 200:
        threat_level += 0.4
    return threat_level



def get_opponent_direction(player_x, player_y, opponents):
    for opponent in opponents:
        opp_x, opp_y = opponent['position']
        if calculate_distance(player_x, player_y, opp_x, opp_y) <= 3:
            return opponent['direction']

    # Default to a random direction if unable to determine the opponent's direction
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
        opp_x, opp_y = opponent['position']
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
    # Increment move count
    move_count += 1
    # Check if it's time to randomly move
    if move_count % 300 == 0:
        return random.choice(['F', 'L', 'R', 'T'])  # Randomly choose a move

    request.get_data()
    player_url, opponents = set_player_and_opponents(request.json)
    # Check if score is increasing
    if player_score > previous_score:
        previous_score = player_score
        return 'T'
    if player_hit:
        consecutive_hits_count += 1
        if consecutive_hits_count >= 3:
            last_hit_direction = get_opponent_direction(player_x, player_y, opponents)
            if last_hit_direction != player_direction:
                if last_hit_direction == 'N':
                    return random.choices(['L', 'R'], weights=[0.7, 0.3])[0]                    
                elif last_hit_direction == 'S':
                    return 'L'
                else:
                    return random.choices(['F', 'R'], weights=[0.7, 0.3])[0]
    # Reset consecutive hits count if not hit in the current turn
    else:
        consecutive_hits_count = 0
    # Check if consecutive hits occurred and move to escape
    if consecutive_hits_count >= 2:
        last_hit_direction = get_opponent_direction(player_x, player_y, opponents)
        if last_hit_direction != player_direction:
            if last_hit_direction == 'N':
                return 'R'
            elif last_hit_direction == 'S':
                return 'L'
            else:
                return 'F'
    # Check if any opponent is in front and within range distance 3
    if is_any_opponent_in_front(player_x, player_y, player_direction, opponents):
        return 'T'
 
    return moves[random.randrange(len(moves))]

if __name__ == "__main__":
  app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))


