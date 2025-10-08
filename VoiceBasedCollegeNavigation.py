import pyttsx3
from collections import deque
import networkx as nx
import matplotlib.pyplot as plt

engine = pyttsx3.init()
engine.setProperty('rate', 160)

def speak(text):
    print(text)
    engine.say(text)
    engine.runAndWait()

college_map = {
    "main gate": ["reception", "parking"],
    "reception": ["main gate", "admin block", "cafeteria"],
    "admin block": ["reception", "cse block", "mba block"],
    "cse block": ["admin block", "library", "auditorium"],
    "library": ["cse block", "auditorium"],
    "auditorium": ["library", "cafeteria"],
    "cafeteria": ["reception", "auditorium", "hostel"],
    "hostel": ["cafeteria"]
}

display_names = {
    "main gate": "Main Gate",
    "reception": "Reception",
    "admin block": "Admin Block",
    "cse block": "CSE Block",
    "library": "Library",
    "auditorium": "Auditorium",
    "cafeteria": "Cafeteria",
    "hostel": "Hostel",
    "parking": "Parking",
    "mba block": "MBA Block"
}

def find_path(start, end):
    visited = set()
    queue = deque([[start]])

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node == end:
            return path

        if node not in visited:
            visited.add(node)
            for neighbour in college_map.get(node, []):
                new_path = list(path)
                new_path.append(neighbour)
                queue.append(new_path)
    return None

def visualize_map(path=None):
    G = nx.Graph()
    for node, neighbors in college_map.items():
        for neighbor in neighbors:
            G.add_edge(node, neighbor)

    pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(10,6))
    nx.draw(G, pos, with_labels=True, labels=display_names, node_color='lightblue', node_size=2000, font_size=10)

    if path:
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_nodes(G, pos, nodelist=path, node_color='orange')
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='red', width=2)

    plt.title("Graphic Era University Campus Map")
    plt.show()

def main():
    speak("Welcome to Graphic Era University Navigation System!")

    print("\nAvailable Locations in the Campus:")
    for key in college_map.keys():
        print("-", display_names.get(key, key.title()))

    start = input("\nEnter your current location: ").lower().strip()
    end = input("Enter your destination: ").lower().strip()

    if start not in college_map or end not in college_map:
        speak("One or both locations are not recognized. Please check the map and try again.")
        return

    path = find_path(start, end)

    if path:
        speak(f"The shortest path from {display_names.get(start, start)} to {display_names.get(end, end)} is:")
        for place in path:
            speak(display_names.get(place, place))
        speak("You have reached your destination.")
        visualize_map(path)
    else:
        speak("Sorry, no path could be found between those locations.")
        visualize_map()

if __name__ == '__main__':
    main()
