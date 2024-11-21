import os
import pandas as pd
from geopy.distance import distance
import networkx as nx
from flask import Flask, request, render_template

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            start_node = request.form['start_node']
            
            # Process the CSV file and calculate the shortest path
            output = process_csv(filepath, start_node)
            return render_template('result.html', output=output, enumerate=enumerate)
    return render_template('index.html')

def process_csv(filepath, start_node):
    # Read the CSV file
    data = pd.read_csv(filepath)
    
    # Create a graph from the locations
    G = nx.Graph()
    for index, row in data.iterrows():
        node_id = str(index)  # Use the row index as the node ID
        G.add_node(node_id, pos=(row['Latitude'], row['Longitude']))
    
    # Calculate distances between all pairs of locations
    distances = {}
    for i in G.nodes:
        for j in G.nodes:
            if i != j:
                lat1, lon1 = G.nodes[i]['pos']
                lat2, lon2 = G.nodes[j]['pos']
                dist = distance((lat1, lon1), (lat2, lon2)).km
                distances[(i, j)] = dist
    
    # Add edges with distances as weights
    for (i, j), dist in distances.items():
        G.add_edge(i, j, weight=dist)
    
    # Find the shortest path visiting all nodes
    route = nx.approximation.traveling_salesman_problem(G, weight='weight')
    route_indices = [int(node_id) for node_id in route]
    
    # Calculate the total distance and approximate time
    total_distance = 0
    for i in range(len(route_indices) - 1):
        source = str(route_indices[i])
        target = str(route_indices[i + 1])
        total_distance += distances[(source, target)]
    
    # Assume an average speed of 40 km/h
    average_speed = 40  # km/h
    total_time = total_distance / average_speed  # in hours
    
    # Prepare the output
    route_details = []
    for index in route_indices:
        row = data.loc[index]
        route_details.append({
            'place_name': row['Place Name'],
            'customer_name': row['Customer Name'],
            'mobile_number': row['Mobile Number']
        })
    
    return {
        'total_time': total_time,
        'total_distance': total_distance,
        'route': route_details
    }

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
