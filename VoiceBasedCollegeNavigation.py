import gradio as gr
from collections import deque
import threading
import os
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

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

# Coordinates for matplotlib (scaled for better visualization)
coordinates = {
    "Gate 1": [0, 0],
    "Gate 2": [1.8, 0.4],
    "Cafeteria": [0.4, 0.3],
    "BTech Block": [0.7, 0.6],
    "Santosh Library": [0.9, 0.9],
    "Ravi Canteen": [1.1, 0.7],
    "Boys Hostel": [1.5, 1.0],
    "CSE Block": [2.0, 0.7]
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

def generate_map_matplotlib(path):
    """Generate a matplotlib map with the route highlighted"""
    if not path or len(path) == 0:
        return None
    
    # Create figure with higher DPI for better quality
    fig, ax = plt.subplots(figsize=(14, 10), dpi=100)
    
    # Set background color
    fig.patch.set_facecolor('#f0f0f0')
    ax.set_facecolor('#ffffff')
    
    # Draw all connections (edges) first in light gray
    for location, neighbors in college_map.items():
        x1, y1 = coordinates[location]
        for neighbor in neighbors:
            x2, y2 = coordinates[neighbor]
            ax.plot([x1, x2], [y1, y2], 'gray', linewidth=1, alpha=0.3, zorder=1)
    
    # Draw the path with arrows and gradient effect
    if len(path) > 1:
        for i in range(len(path) - 1):
            x1, y1 = coordinates[path[i]]
            x2, y2 = coordinates[path[i + 1]]
            
            # Draw thick path line
            ax.plot([x1, x2], [y1, y2], 'red', linewidth=4, alpha=0.7, zorder=2)
            
            # Add arrow
            arrow = FancyArrowPatch(
                (x1, y1), (x2, y2),
                arrowstyle='->', 
                color='darkred', 
                linewidth=2,
                mutation_scale=20,
                zorder=3
            )
            ax.add_patch(arrow)
    
    # Plot all locations as nodes
    for place, coord in coordinates.items():
        x, y = coord
        
        if place == path[0]:
            # Start location - large green circle
            circle = plt.Circle((x, y), 0.08, color='green', alpha=0.8, zorder=4)
            ax.add_patch(circle)
            ax.plot(x, y, 'o', color='darkgreen', markersize=20, zorder=5)
            ax.text(x, y-0.15, '🚀 START', ha='center', va='top', 
                   fontsize=10, fontweight='bold', color='green',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='green', linewidth=2))
            
        elif place == path[-1]:
            # End location - large red circle with flag
            circle = plt.Circle((x, y), 0.08, color='red', alpha=0.8, zorder=4)
            ax.add_patch(circle)
            ax.plot(x, y, 'o', color='darkred', markersize=20, zorder=5)
            ax.text(x, y-0.15, '🏁 DESTINATION', ha='center', va='top', 
                   fontsize=10, fontweight='bold', color='red',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', linewidth=2))
            
        elif place in path:
            # Waypoint - orange circle with step number
            step_num = path.index(place) + 1
            circle = plt.Circle((x, y), 0.06, color='orange', alpha=0.8, zorder=4)
            ax.add_patch(circle)
            ax.plot(x, y, 'o', color='darkorange', markersize=16, zorder=5)
            ax.text(x, y, str(step_num), ha='center', va='center', 
                   fontsize=11, fontweight='bold', color='white', zorder=6)
            
        else:
            # Other locations - blue circles
            circle = plt.Circle((x, y), 0.05, color='lightblue', alpha=0.6, zorder=4)
            ax.add_patch(circle)
            ax.plot(x, y, 'o', color='blue', markersize=12, zorder=5)
        
        # Add location labels
        label_y_offset = 0.12 if place not in [path[0], path[-1]] else 0.25
        ax.text(x, y+label_y_offset, place, ha='center', va='bottom', 
               fontsize=9, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                        edgecolor='black', alpha=0.7, linewidth=1))
    
    # Add step numbers for path locations
    for idx, place in enumerate(path):
        x, y = coordinates[place]
        if place not in [path[0], path[-1]]:  # Skip start and end
            ax.text(x+0.15, y+0.15, f'Step {idx+1}', ha='left', va='bottom',
                   fontsize=8, style='italic', color='darkred',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='lightyellow', alpha=0.8))
    
    # Set axis properties
    ax.set_xlim(-0.3, 2.3)
    ax.set_ylim(-0.3, 1.3)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Title and labels
    route_str = " → ".join(path)
    ax.set_title(f'🗺️ GEU Campus Navigation Map\nRoute: {route_str}', 
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Campus West → East', fontsize=11, fontweight='bold')
    ax.set_ylabel('Campus South → North', fontsize=11, fontweight='bold')
    
    # Add legend
    legend_elements = [
        mpatches.Patch(color='green', label='Start Location'),
        mpatches.Patch(color='red', label='Destination'),
        mpatches.Patch(color='orange', label='Waypoints'),
        mpatches.Patch(color='lightblue', label='Other Locations'),
        mpatches.Patch(color='red', alpha=0.7, label='Suggested Route')
    ]
    ax.legend(handles=legend_elements, loc='upper right', 
             fontsize=9, framealpha=0.9, edgecolor='black')
    
    # Tight layout
    plt.tight_layout()
    
    # Save to temporary file
    try:
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.png', 
            mode='wb'
        )
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight', 
                   facecolor='#f0f0f0', edgecolor='none')
        plt.close(fig)
        return temp_file.name
    except Exception as e:
        print(f"Error generating map: {e}")
        plt.close(fig)
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
    
    # Generate matplotlib map
    map_file = generate_map_matplotlib(path)
    
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
    
    return result_message, map_file, voice_text

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
            map_output = gr.Image(label="Route Visualization", type="filepath")
    
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
    5. 🗺️ Follow the numbered waypoints on the map
    
    ### 🎨 Features:
    
    - ⚡ **BFS Algorithm** for shortest path calculation
    - 🎤 **Voice Guidance** with step-by-step instructions
    - 🗺️ **Matplotlib Visualization** with color-coded markers
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
