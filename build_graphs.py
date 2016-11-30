#!/usr/bin/env python
import networkx as nx

airport_schema = {
        'airport_id' : 0,
        'name' : 1,
        'city' : 2,
        'country': 3,
        'iata/faa' : 4,
        'icao': 5,
        'latitude' : 6,
        'longitude' : 7,
        'altitude' : 8,
        'timezone' : 9,
        'dst' : 10,
        'tz_database' : 11
        }


routes_schema = {
        'airline' : 0,
        'airline_id' : 1,
        'source_airport' : 2,
        'source_airport_id' : 3,
        'destination_airport' : 4,
        'destination_airport_id' : 5,
        'codeshare' : 6,
        'stops' : 7,
        'equipment' : 8
        }


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    hlat = sin(dlat/2)**2
    hlon = sin(dlon/2)**2
    a = hlat + cos(lat1) * cos(lat2) * hlon
    c = 2 * asin(sqrt(a))
    # earth's radius varies between 6356 to 6378 km so 6367 is the average of the two
    km = 6367 * c
    return km

def get_airport_data():
    airport_data = {}
    with open('airports.dat', 'r') as f:
        data = f.read().split('\n')
        data.pop()
        data = map(lambda x: map(lambda y: y.strip('"'), x), map(lambda z: z.split(','), data))
        for row in data:
            airport_data[row[airport_schema['airport_id']]] = {
                    k: row[airport_schema[k]]
                    for k in airport_schema.keys()
                    } 
    with open('routes.dat', 'r') as f:
        data = f.read().split('\n')
        data.pop()
        data = map(lambda x: map(lambda y: y.strip('"'), x.split(',')), data)
        for r in data:
            src_id = r[routes_schema['source_airport_id']]
            dst_id = r[routes_schema['destination_airport_id']]
            if airport_data.get(src_id):
                if not airport_data[src_id].get('count'):
                    airport_data[src_id]['count'] = 1
                else:
                    airport_data[src_id]['count'] += 1
            if airport_data.get(dst_id):
                if not airport_data[dst_id].get('count'):
                    airport_data[dst_id]['count'] = 1
                else:
                    airport_data[dst_id]['count'] += 1
    # sanity check for the 'count' key
    for r in airport_data.keys():
        if not airport_data[r].get('count'):
            airport_data[r]['count'] = 0
    return airport_data

def parse_routes():
    airport_data = get_airport_data()
    airport_graph = nx.Graph()
    with open('routes.dat', 'r') as f:
        data = f.read().split('\n')
        data.pop()
        data = map(lambda x: map(lambda y: y.strip('"'), x), map(lambda z: z.split(','), data))
        for row in data:
            source_airport_id = row[routes_schema['source_airport_id']]
            dest_airport_id = row[routes_schema['destination_airport_id']]
            airline_id = row[routes_schema['airline_id']]
            try:
                lat1, lon1 = float(airport_data[source_airport_id]['latitude']), float(airport_data[source_airport_id]['longitude'])
                lat2, lon2 = float(airport_data[dest_airport_id]['latitude']), float(airport_data[dest_airport_id]['longitude'])
                dist = haversine(lat1, lon1, lat2, lon2)
            except Exception, e:
                continue
            airport_graph.add_edge(source_airport_id, dest_airport_id, attr_dict={'distance' : dist})
    return airport_graph


def find_airports(city, airportdata=None, state=None, country=None):
    if not airportdata:
        airportdata = get_airport_data()
    return sorted(map(lambda x: airportdata[x], filter(lambda y: city.lower() in airportdata[y]['city'].lower(), airportdata.keys())), key=lambda x: x['count'])



def optimize_paths_distance_hops(start, end):
    """
    Parameters
    ----------
    start : str city name for start
    end : str city name for end

    Returns
    ---------
    paths : list of paths to take
    """
    airport_graph = parse_routes()
    nodes_to_traverse = []
    paths = {}
    for n in airport_graph[start].keys():
        nodes_to_traverse.append( n )       
        paths[n] = {
                'distance' : airport_graph.get_edge_data(start, n)['distance'], 
                'path' : [start, n],
                'paths' : []
                }
    while len(nodes_to_traverse) > 0:
        n = nodes_to_traverse[0]
        del nodes_to_traverse[0]
        for n1 in airport_graph[n].keys():
            if not paths.get(n1):
                paths[n1] = {
                        'distance' : paths[n]['distance'] + airport_graph.get_edge_data(n, n1)['distance'],
                        'path' : paths[n]['path'] + [n1],
                        'paths' : [ paths[n]['path'] + [n1] ]
                        }
                nodes_to_traverse.append(n1)
            else:
                paths[n1]['paths'].append(paths[n]['path'] + [n1])
                if paths[n1]['distance'] > paths[n]['distance'] + airport_graph.get_edge_data(n, n1)['distance'] and len(paths[n1]['path']) >= len(paths[n]['path'] + [n1]):
                    paths[n1]['path'] = paths[n]['path'] + [n1]
                    paths[n1]['distance'] = paths[n]['distance'] + airport_graph.get_edge_data(n, n1)['distance']
    return paths[end]


if __name__ == '__main__':
    print '''
    Calculates the shortest path by distance and hops between two cities
    and plans the travel route, irrespective of any other factors
    '''
    airportdata = get_airport_data()    
    start = raw_input("Enter a start city:")    
    start_airports = list(reversed(find_airports(start, airportdata=airportdata)))[0:3]
    for ix, a in enumerate(start_airports):
        print ix, a['name']
    print ''
    start_selection = raw_input("Please type the number for the airport you would like to depart from: ")
    start_airport = start_airports[int(start_selection)]
    end = raw_input("Enter an destination city:")
    end_airports = list(reversed(find_airports(end, airportdata=airportdata)))[0:3]
    for ix, a in enumerate(end_airports):
        print ix, a['name']
    end_selection = raw_input("Please type the number for the airport you would like to depart from: ")
    end_airport = end_airports[int(end_selection)]
    start_id = start_airport['airport_id']
    end_id = end_airport['airport_id']
    path = optimize_paths_distance_hops(start_id, end_id)        
    print path
    print ''
    print "Total distance: %f km" % path['distance']
    print ' --> '.join([airportdata[i]['iata/faa'] for i in path['path']])
    print ''        
    for i in range(len(path['path'])):
        print "Airport %d: %s, %s, %s" % (i, airportdata[path['path'][i]]['iata/faa'], airportdata[path['path'][i]]['city'], airportdata[path['path'][i]]['country'])
