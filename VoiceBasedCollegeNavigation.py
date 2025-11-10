from flask import Flask, render_template, request, jsonify
import folium
import pyttsx3
from collections import deque
import os

app = Flask(__name__)

engine = pyttsx3.init()
engine.setProperty('rate', 160)

# ---- Campus Map ----
college_map = {
    "gate 1": ["cafeteria", "gate 2"],
    "gate 2": ["gate 1", "cse block", "boys hostel"],
    "cafeteria": ["gate 1", "btech block"],
    "btech block": ["cafeteria", "santosh library", "ravi canteen"],
    "santosh library": ["btech block"],
    "ravi canteen": ["btech block", "boys hostel"],
    "boys hostel": ["ravi canteen", "cse block"],
    "cse block": ["gate 2", "boys hostel"]
}

# Coordinates (approximate for Folium map)
coordinates = {
    "gate 1": [30.2730, 78.9990],
    "gate 2": [30.2748, 78.9994],
    "cafeteria": [30.2734, 78.9993],
    "btech block": [30.2737, 78.9996],
    "santosh library": [30.2739, 78.9999],
    "ravi canteen": [30.2741, 78.9997],
    "boys hostel": [30.2745, 79.0000],
    "cse block": [30.2750, 78.9997]
}

def speak(text):
    """Voice output"""
    print("Voice:", text)
    engine.say(text)
    engine.runAndWait()

def find_path(start, end):
    """BFS Shortest Path"""
    visited = set()
    queue = deque([[start]])
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == end:
            return path
        if node not in visited:
            visited.add(node)
            for neighbor in college_map.get(node, []):
                new_path = list(path)
                new_path.append(neighbor)
                queue.append(new_path)
    return None

def generate_map(path):
    """Generate a map with route highlighted"""
    start = path[0]
    m = folium.Map(location=coordinates[start], zoom_start=18)

    # Add markers
    for place, coord in coordinates.items():
        folium.Marker(coord, popup=place.title(), tooltip=place.title()).add_to(m)

    # Draw path line
    path_coords = [coordinates[p] for p in path]
    folium.PolyLine(path_coords, color="red", weight=5, opacity=0.8).add_to(m)

    # Save to HTML
    map_path = os.path.join("templates", "map.html")
    m.save(map_path)
    return map_path

@app.route('/')
def index():
    locations = list(college_map.keys())
    return render_template('index.html', locations=locations)

@app.route('/navigate', methods=['POST'])
def navigate():
    data = request.json
    start = data.get('start', '').lower().strip()
    end = data.get('end', '').lower().strip()

    if start not in college_map or end not in college_map:
        speak("Invalid locations selected.")
        return jsonify({'error': 'Invalid locations selected'})

    path = find_path(start, end)
    if not path:
        speak("No path found between selected points.")
        return jsonify({'error': 'No path found'})

    # Voice Instructions
    speak(f"Starting from {start}.")
    for place in path[1:]:
        speak(f"Proceed to {place}.")
    speak("You have reached your destination.")

    generate_map(path)
    return jsonify({'path': path, 'map': '/map'})

@app.route('/map')
def show_map():
    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=True)
