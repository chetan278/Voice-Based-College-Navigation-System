import gradio as gr
import folium
from collections import deque
import threading
import os
import tempfile
from pathlib import Path

# Try to import pyttsx3, but make it optional
try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    voice_enabled = True
except Exception as e:
    voice_enabled = False
    print(f"Voice engine not available: {e}")

# ---- Campus Map ----
college_map = {
    "Gate 1": ["Cafeteria", "Gate 2"],
    "Gate 2": ["Gate 1", "CSE Block", "Boys Hostel"],
    "Cafeteria": ["Gate 1", "BTech Block"],
    "BTech Block": ["Cafeteria", "Santosh Library", "Ravi Canteen"],
    "Santosh Library": ["BTech Block"],
    "Ravi Canteen": ["BTech Block", "Boys Hostel"],
    "Boys Hostel": ["Ravi Canteen", "Gate 2", "CSE Block"],
    "CSE Block": ["Gate 2", "Boys Hostel"]
}

# Coordinates (approximate for Folium map)
coordinates = {
    "Gate 1": [30.2730, 78.9990],
    "Gate 2": [30.2748, 78.9994],
    "Cafeteria": [30.2734, 78.9993],
    "BTech Block": [30.2737, 78.9996],
    "Santosh Library": [30.2739, 78.9999],
    "Ravi Canteen": [30.2741, 78.9997],
    "Boys Hostel": [30.2745, 79.0000],
    "CSE Block": [30.2750, 78.9997]
}

def speak_async(text):
    """Non-blocking voice output using threading"""
    if voice_enabled:
        def _speak():
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"Voice error: {e}")
        
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()

def find_path(start, end):
    """BFS Shortest Path Algorithm"""
    if start == end:
        return [start]
    
    if start not in college_map or end not in college_map:
        return None
    
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
    """Generate an interactive Folium map with the route highlighted"""
    if not path or len(path) == 0:
        return None
    
    start = path[0]
    # Center map on starting location
    m = folium.Map(
        location=coordinates[start], 
        zoom_start=17,
        tiles='OpenStreetMap'
    )

    # Add markers for all locations
    for place, coord in coordinates.items():
        if place == path[0]:
            # Start location - green
            icon = folium.Icon(color='green', icon='play', prefix='fa')
            popup_text = f"<b>START: {place}</b>"
        elif place == path[-1]:
            # End location - red
            icon = folium.Icon(color='red', icon='flag-checkered', prefix='fa')
            popup_text = f"<b>DESTINATION: {place}</b>"
        elif place in path:
            # Waypoint - orange
            icon = folium.Icon(color='orange', icon='info-sign')
            popup_text = f"<b>Waypoint: {place}</b>"
        else:
            # Other locations - blue
            icon = folium.Icon(color='blue', icon='info-sign')
            popup_text = f"<b>{place}</b>"
        
        folium.Marker(
            coord, 
            popup=popup_text, 
            tooltip=place,
            icon=icon
        ).add_to(m)

    # Draw path line if more than one location
    if len(path) > 1:
        path_coords = [coordinates[p] for p in path]
        folium.PolyLine(
            path_coords, 
            color="red", 
            weight=5, 
            opacity=0.7,
            popup="<b>Your Route</b>"
        ).add_to(m)
        
        # Add numbered circle markers for each step
        for idx, place in enumerate(path):
            folium.CircleMarker(
                location=coordinates[place],
                radius=12,
                popup=f"<b>Step {idx + 1}: {place}</b>",
                color='darkred',
                fill=True,
                fillColor='red',
                fillOpacity=0.6,
                weight=2
            ).add_to(m)
            
            # Add step numbers as overlay
            folium.Marker(
                location=coordinates[place],
                icon=folium.DivIcon(
                    html=f'''<div style="
                        font-size: 11pt; 
                        color: white; 
                        font-weight: bold;
                        text-align: center;
                        text-shadow: 1px 1px 2px black;
                    ">{idx + 1}</div>'''
                )
            ).add_to(m)

    # Save to temporary HTML file
    try:
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.html', 
            mode='w',
            encoding='utf-8'
        )
        m.save(temp_file.name)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        print(f"Error generating map: {e}")
        return None

def calculate_distance(path):
    """Calculate approximate distance based on path length"""
    if not path or len(path) < 2:
        return 0
    # Assuming average 80-120 meters between adjacent locations
    return (len(path) - 1) * 100

def navigate(start_location, end_location, enable_voice):
    """Main navigation function"""
    
    # Validation
    if not start_location or not end_location:
        return "⚠️ Please select both start and destination locations.", None, ""
    
    if start_location not in college_map or end_location not in college_map:
        return "❌ Invalid location selected.", None, ""
    
    # Same location check
    if start_location == end_location:
        message = f"✅ You are already at **{start_location}**!"
        if enable_voice:
            speak_async(f"You are already at {start_location}")
        return message, None, ""
    
    # Find shortest path using BFS
    path = find_path(start_location, end_location)
    
    if not path:
        message = f"❌ No path found between **{start_location}** and **{end_location}**."
        if enable_voice:
            speak_async(message)
        return message, None, ""
    
    # Generate voice instructions
    voice_instructions = []
    if enable_voice:
        speak_async(f"Starting navigation from {start_location} to {end_location}.")
        voice_instructions.append(f"🎯 Starting from **{start_location}**")
        
        for i, place in enumerate(path[1:], 1):
            instruction = f"Step {i}: Proceed to **{place}**"
            speak_async(f"Step {i}. Proceed to {place}.")
            voice_instructions.append(instruction)
        
        speak_async("You have reached your destination.")
        voice_instructions.append(f"🏁 Destination reached: **{end_location}**")
    
    # Generate interactive map
    map_file = generate_map(path)
    
    # Create result message
    path_str = " → ".join(path)
    distance = calculate_distance(path)
    
    result_message = f"""
## ✅ Navigation Successful!

**Route:** {path_str}

**Total Steps:** {len(path)} locations

**Estimated Distance:** ~{distance} meters

**Estimated Walking Time:** ~{distance // 80} minutes
"""
    
    # Voice instructions text
    voice_text = "\n".join(voice_instructions) if voice_instructions else "🔇 Voice navigation disabled"
    
    # Read map file and return HTML content
    map_html = None
    if map_file and os.path.exists(map_file):
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                map_html = f.read()
            # Clean up temp file after reading
            os.unlink(map_file)
        except Exception as e:
            print(f"Error reading map file: {e}")
    
    return result_message, map_html, voice_text

# Create Gradio Interface
with gr.Blocks(title="🎓 GEU Campus Navigation", theme=gr.themes.Soft()) as app:
    
    gr.Markdown("""
    # 🎓 GEU Campus Voice Navigation System
    ### Find the shortest path between any two locations on campus
    *Powered by BFS Algorithm & Voice Guidance*
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📍 Navigation Controls")
            
            start_dropdown = gr.Dropdown(
                choices=sorted(college_map.keys()),
                label="🚀 Start Location",
                value="Gate 1",
                interactive=True
            )
            
            end_dropdown = gr.Dropdown(
                choices=sorted(college_map.keys()),
                label="🎯 Destination",
                value="CSE Block",
                interactive=True
            )
            
            voice_checkbox = gr.Checkbox(
                label="🔊 Enable Voice Navigation",
                value=voice_enabled,
                info="Real-time voice instructions" if voice_enabled else "Voice not available",
                interactive=voice_enabled
            )
            
            navigate_btn = gr.Button(
                "🧭 Start Navigation", 
                variant="primary", 
                size="lg"
            )
            
            gr.Markdown("---")
            
            result_text = gr.Markdown(label="📊 Navigation Result")
            
            voice_output = gr.Textbox(
                label="📢 Voice Instructions",
                lines=8,
                interactive=False,
                placeholder="Voice instructions will appear here..."
            )
        
        with gr.Column(scale=2):
            gr.Markdown("### 🗺️ Interactive Campus Map")
            map_output = gr.HTML(label="Route Visualization")
    
    gr.Markdown("""
    ---
    ### 📋 Available Campus Locations:
    
    **Main Entrances:** Gate 1 • Gate 2  
    **Dining:** Cafeteria • Ravi Canteen  
    **Academic:** BTech Block • CSE Block  
    **Facilities:** Santosh Library • Boys Hostel
    
    ### ℹ️ How to Use:
    
    1. 📍 Select your **current location** from the dropdown
    2. 🎯 Choose your **destination**
    3. 🔊 Toggle voice navigation (if available)
    4. 🧭 Click **Start Navigation** to get the shortest route
    5. 🗺️ Follow the numbered waypoints on the interactive map
    
    ### 🔍 Features:
    
    - ⚡ **BFS Algorithm** for shortest path calculation
    - 🎤 **Voice Guidance** with step-by-step instructions
    - 🗺️ **Interactive Map** with color-coded markers
    - 📏 **Distance Estimation** for route planning
    """)
    
    # Event handler
    navigate_btn.click(
        fn=navigate,
        inputs=[start_dropdown, end_dropdown, voice_checkbox],
        outputs=[result_text, map_output, voice_output]
    )
    
    # Quick Navigation Examples
    gr.Examples(
        examples=[
            ["Gate 1", "CSE Block", True],
            ["Cafeteria", "Boys Hostel", True],
            ["Gate 2", "Santosh Library", False],
            ["BTech Block", "Gate 1", True],
            ["Ravi Canteen", "Gate 2", False],
        ],
        inputs=[start_dropdown, end_dropdown, voice_checkbox],
        outputs=[result_text, map_output, voice_output],
        fn=navigate,
        cache_examples=False,
        label="🎯 Quick Navigation Examples"
    )

# Launch the app
if __name__ == "__main__":
    print("=" * 70)
    print("🎓 GEU CAMPUS NAVIGATION SYSTEM")
    print("=" * 70)
    print(f"Voice Support: {'✅ Enabled' if voice_enabled else '❌ Disabled'}")
    print(f"Available Locations: {len(college_map)}")
    print("=" * 70)
    print("Starting Gradio interface...")
    print("=" * 70)
    
    app.launch(
        share=False,
        inbrowser=True,
        server_name="0.0.0.0",  # Allow network access
        server_port=7860,
        show_error=True
    )
