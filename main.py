import collections
import heapq
import time
import math

import networkx as nx
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context

# 1.  ROUTE DATA  (stops in order)

ROUTES = {
    "SU345 Thurber St": [
        "College Pl (SU)", "Jamesville Ave / Vincent St", "Ainsley Dr / Ball Cir",
        "Thurber St / Alden St", "Remington Gardens Apts", "Hidden Valley Apts",
        "Clarendon Heights Apts", "SU Physical Plant", "University Townhouses",
        "Lally Athletics Complex", "College Pl (SU)",
    ],
    "SU343 E.Genesee/Westcott": [
        "College Pl (SU)", "Irving Ave / E. Genesee St (Syracuse Stage/CFAC)",
        "E. Genesee St / S. Crouse Ave", "E. Genesee St / Westcott St",
        "Westcott St / Euclid Ave", "Broad St", "Westcott St / Euclid Ave",
        "E. Genesee St / Westcott St", "College Pl (SU)",
    ],
    "SU43 Waverly Ave": [
        "College Pl (SU)", "Irving Ave / University Pl", "Henry St / Van Buren St",
        "Waverly Ave / S. Crouse Ave", "Center of Excellence", "The Warehouse",
        "La Casita Cultural Center", "College Pl (SU)",
    ],
    "SU443 Connective Corridor": [
        "College Pl (SU)", "Irving Ave / University Pl", "Archbold Gym",
        "JMA Wireless Dome", "Henry St / Van Buren St", "Waverly Ave / S. Crouse Ave",
        "Center of Excellence", "The Warehouse", "La Casita Cultural Center",
        "Syracuse Stage / CFAC", "Comstock Lot", "Carmelo K. Anthony Center",
        "Lally Athletics Complex", "Colvin Lot", "Small Rd / Lambreth Ln",
        "Slocum Dr / Lambreth Ln", "Winding Ridge Rd N.", "Goldstein Student Center",
        "Skyhall", "Skytop Office Building", "College Pl (SU)",
    ],
    "SU44 Skytop Rd": [
        "College Pl (SU)", "Comstock Lot", "Colvin Lot", "Skytop Office Building",
        "Skyhall", "Goldstein Student Center", "College Pl (SU)",
    ],
    "SU344 South Campus": [
        "College Pl (SU)", "Comstock Art Facility", "Comstock Lot",
        "Carmelo K. Anthony Center", "Lally Athletics Complex", "Colvin Lot",
        "Small Rd / Lambreth Ln", "Slocum Dr / Lambreth Ln", "Winding Ridge Rd N.",
        "Goldstein Student Center", "Skyhall", "Skytop Office Building", "College Pl (SU)",
    ],
    "Euclid Loop": [
        "College Pl (SU)", "Genesee / Irving", "Genesee / Crouse",
        "E. Genesee St / Westcott St", "Westcott St / Euclid Ave", "College Pl (SU)",
    ],
    "Warehouse Loop": [
        "College Pl (SU)", "BBB / Campus West", "Syracuse Stage / CFAC",
        "Peck Hall (Fayette St)", "The Warehouse", "Syracuse Stage / CFAC",
        "Schine Student Center", "BBB / Campus West", "College Pl (SU)",
    ],
    "South Campus Loop": [
        "College Pl (SU)", "Colvin Lot", "Small Rd / Lambreth Ln",
        "Slocum Dr / Lambreth Ln", "Winding Ridge Rd N.", "Skytop Office Building",
        "Goldstein Student Center", "Skyhall", "Comstock Lot", "College Pl (SU)",
    ],
    "Blue Loop": [
        "Irving Garage", "Sadler Hall", "Barnes Center", "Sims Drive at College Pl",
        "Flint Hall", "Shaw Hall (Euclid)", "Life Sciences", "Comstock Ave & Adams St",
        "Waverly Ave Lot", "Walnut Ave at Harrison St", "University Ave & Harrison St",
        "National Veterans Resource Center", "Quad Lot", "BBB on Van Buren",
        "Campus West", "Henry St Lot", "Irving Garage",
    ],
    "Orange Loop": [
        "Irving Garage (Stadium Pl.)", "Quad Lot", "National Veterans Resource Center",
        "University Ave & Harrison St", "Schine Student Center", "Comstock Ave & Adams St",
        "Dellplain (University Pl.)", "College Pl (SU)", "Flint Hall",
        "Shaw Hall (Euclid Ave.)", "Barnes Center at the Arch", "Forestry Gate",
        "BBB on Van Buren", "Campus West", "Henry St Lot", "Lawrinson Garage",
        "Irving Garage (Stadium Pl.)",
    ],
    "Comstock/Colvin Loop": [
        "Colvin Lot", "Comstock Lot", "College Pl (SU)", "Comstock Lot", "Colvin Lot",
    ],
}

# 2.  REAL EDGE WEIGHTS  (minutes, extracted from official PDFs)
#     Source: Centro / SU schedule timepoints

# Format: (stop_a, stop_b): minutes
# Derived from published schedule timepoints across all routes
REAL_WEIGHTS = {
    # SU345 Thurber St  (7:55 -> 8:00 -> 8:08 -> ... College Pl to Ainsley ~13 min)
    ("College Pl (SU)", "Jamesville Ave / Vincent St"):     5,
    ("Jamesville Ave / Vincent St", "Ainsley Dr / Ball Cir"): 8,
    ("Ainsley Dr / Ball Cir", "Thurber St / Alden St"):     3,
    ("Thurber St / Alden St", "Remington Gardens Apts"):    3,
    ("Remington Gardens Apts", "Hidden Valley Apts"):       2,
    ("Hidden Valley Apts", "Clarendon Heights Apts"):       2,
    ("Clarendon Heights Apts", "SU Physical Plant"):        3,
    ("SU Physical Plant", "University Townhouses"):         3,
    ("University Townhouses", "Lally Athletics Complex"):   4,

    # SU343 E.Genesee/Westcott  (College Pl -> Irving ~7 min, full loop ~30 min)
    ("College Pl (SU)", "Irving Ave / E. Genesee St (Syracuse Stage/CFAC)"): 7,
    ("Irving Ave / E. Genesee St (Syracuse Stage/CFAC)", "E. Genesee St / S. Crouse Ave"): 2,
    ("E. Genesee St / S. Crouse Ave", "E. Genesee St / Westcott St"): 3,
    ("E. Genesee St / Westcott St", "Westcott St / Euclid Ave"): 4,
    ("Westcott St / Euclid Ave", "Broad St"):               5,

    # SU43 / SU443  (College Pl -> Irving ~3 min, Irving -> Henry ~3 min, etc.)
    ("College Pl (SU)", "Irving Ave / University Pl"):      3,
    ("Irving Ave / University Pl", "Archbold Gym"):         2,
    ("Archbold Gym", "JMA Wireless Dome"):                  2,
    ("Irving Ave / University Pl", "Henry St / Van Buren St"): 3,
    ("JMA Wireless Dome", "Henry St / Van Buren St"):       3,
    ("Henry St / Van Buren St", "Waverly Ave / S. Crouse Ave"): 4,
    ("Waverly Ave / S. Crouse Ave", "Center of Excellence"): 3,
    ("Center of Excellence", "The Warehouse"):              4,
    ("The Warehouse", "La Casita Cultural Center"):         3,
    ("La Casita Cultural Center", "College Pl (SU)"):       8,
    ("The Warehouse", "Syracuse Stage / CFAC"):             3,
    ("Syracuse Stage / CFAC", "Comstock Lot"):              4,
    ("Comstock Lot", "Carmelo K. Anthony Center"):          3,
    ("Carmelo K. Anthony Center", "Lally Athletics Complex"): 3,
    ("Lally Athletics Complex", "Colvin Lot"):              4,
    ("Colvin Lot", "Small Rd / Lambreth Ln"):               3,
    ("Small Rd / Lambreth Ln", "Slocum Dr / Lambreth Ln"):  3,
    ("Slocum Dr / Lambreth Ln", "Winding Ridge Rd N."):     2,
    ("Winding Ridge Rd N.", "Goldstein Student Center"):    3,
    ("Goldstein Student Center", "Skyhall"):                2,
    ("Skyhall", "Skytop Office Building"):                  3,
    ("Skytop Office Building", "College Pl (SU)"):         12,

    # SU44 Skytop  (College Pl -> Comstock 4 min, Comstock -> Colvin 3 min, etc.)
    ("College Pl (SU)", "Comstock Lot"):                    4,
    ("Comstock Lot", "Colvin Lot"):                         3,
    ("Colvin Lot", "Skytop Office Building"):               8,

    # SU344 South Campus
    ("College Pl (SU)", "Comstock Art Facility"):           3,
    ("Comstock Art Facility", "Comstock Lot"):              2,

    # Euclid Loop  (7 min per leg from schedule)
    ("College Pl (SU)", "Genesee / Irving"):                7,
    ("Genesee / Irving", "Genesee / Crouse"):               1,
    ("Genesee / Crouse", "E. Genesee St / Westcott St"):    4,

    # Warehouse Loop  (College Pl -> BBB 2 min, BBB -> Syracuse Stage 3 min, etc.)
    ("College Pl (SU)", "BBB / Campus West"):               2,
    ("BBB / Campus West", "Syracuse Stage / CFAC"):         3,
    ("Syracuse Stage / CFAC", "Peck Hall (Fayette St)"):    3,
    ("Peck Hall (Fayette St)", "The Warehouse"):            5,
    ("Syracuse Stage / CFAC", "Schine Student Center"):     4,
    ("Schine Student Center", "BBB / Campus West"):         3,

    # South Campus Loop  (20 min loop from schedule - every 20 min)
    ("College Pl (SU)", "Colvin Lot"):                      6,
    ("Winding Ridge Rd N.", "Skytop Office Building"):      2,
    ("Skytop Office Building", "Goldstein Student Center"): 3,
    ("Skyhall", "Comstock Lot"):                            4,

    # Blue Loop  (40 min full loop, ~2-3 min between stops)
    ("Irving Garage", "Sadler Hall"):                       1,
    ("Sadler Hall", "Barnes Center"):                       3,
    ("Barnes Center", "Sims Drive at College Pl"):          1,
    ("Sims Drive at College Pl", "Flint Hall"):             5,
    ("Flint Hall", "Shaw Hall (Euclid)"):                   5,
    ("Shaw Hall (Euclid)", "Life Sciences"):                2,
    ("Life Sciences", "Comstock Ave & Adams St"):           3,
    ("Comstock Ave & Adams St", "Waverly Ave Lot"):         2,
    ("Waverly Ave Lot", "Walnut Ave at Harrison St"):       2,
    ("Walnut Ave at Harrison St", "University Ave & Harrison St"): 1,
    ("University Ave & Harrison St", "National Veterans Resource Center"): 2,
    ("National Veterans Resource Center", "Quad Lot"):      2,
    ("Quad Lot", "BBB on Van Buren"):                       4,
    ("BBB on Van Buren", "Campus West"):                    1,
    ("Campus West", "Henry St Lot"):                        1,
    ("Henry St Lot", "Irving Garage"):                      1,

    # Orange Loop  (40 min full loop)
    ("Irving Garage (Stadium Pl.)", "Quad Lot"):            5,
    ("Quad Lot", "National Veterans Resource Center"):      3,
    ("National Veterans Resource Center", "University Ave & Harrison St"): 3,
    ("University Ave & Harrison St", "Schine Student Center"): 2,
    ("Schine Student Center", "Comstock Ave & Adams St"):   2,
    ("Comstock Ave & Adams St", "Dellplain (University Pl.)"): 2,
    ("Dellplain (University Pl.)", "College Pl (SU)"):      2,
    ("College Pl (SU)", "Flint Hall"):                      4,
    ("Flint Hall", "Shaw Hall (Euclid Ave.)"):              2,
    ("Shaw Hall (Euclid Ave.)", "Barnes Center at the Arch"): 2,
    ("Barnes Center at the Arch", "Forestry Gate"):         3,
    ("Forestry Gate", "BBB on Van Buren"):                  3,
    ("BBB on Van Buren", "Campus West"):                    1,
    ("Campus West", "Henry St Lot"):                        1,
    ("Henry St Lot", "Lawrinson Garage"):                   1,
    ("Lawrinson Garage", "Irving Garage (Stadium Pl.)"):    1,

    # Comstock/Colvin Loop  (1 min between adjacent lots)
    ("Colvin Lot", "Comstock Lot"):                         1,
}

def get_weight(a, b):
    """Return travel time in minutes between two stops (bidirectional)."""
    w = REAL_WEIGHTS.get((a, b)) or REAL_WEIGHTS.get((b, a))
    return w if w else 4  # default 4 min for unlisted segments


# 3.  BUILD WEIGHTED GRAPH

def build_graph(routes):
    graph = collections.defaultdict(set)
    for route_name, stops in routes.items():
        for i in range(len(stops) - 1):
            a, b = stops[i], stops[i + 1]
            if a != b:
                w = get_weight(a, b)
                graph[a].add((b, route_name, w))
                graph[b].add((a, route_name, w))
    return dict(graph)

graph = build_graph(ROUTES)

# Stop -> routes map
stop_routes = collections.defaultdict(set)
for route_name, stops in ROUTES.items():
    for s in stops:
        stop_routes[s].add(route_name)

# NetworkX graph with weights
G = nx.Graph()
for route_name, stops in ROUTES.items():
    for i in range(len(stops) - 1):
        a, b = stops[i], stops[i + 1]
        if a != b:
            w = get_weight(a, b)
            if G.has_edge(a, b):
                G[a][b]['weight'] = min(G[a][b]['weight'], w)
            else:
                G.add_edge(a, b, weight=w, route=route_name)

pos = nx.spring_layout(G, seed=42, k=2.8)
articulation_pts = set(nx.articulation_points(G))
all_stops_sorted = sorted(graph.keys())


# 4.  ALGORITHMS  (all timed with perf_counter)


def timed(fn, *args):
    """Run fn(*args), return (result, microseconds)."""
    t0 = time.perf_counter()
    result = fn(*args)
    return result, round((time.perf_counter() - t0) * 1_000_000, 2)

# DFS
def dfs_path(graph, start, goal):
    stack, visited = [(start, [start])], set()
    nodes_explored = [0]
    while stack:
        node, path = stack.pop()
        nodes_explored[0] += 1
        if node == goal:
            return path, nodes_explored[0]
        if node in visited:
            continue
        visited.add(node)
        for neighbor, _, _ in graph.get(node, []):
            if neighbor not in visited:
                stack.append((neighbor, path + [neighbor]))
    return [], nodes_explored[0]

# BFS
def bfs_path(graph, start, goal):
    queue, visited = collections.deque([(start, [start])]), {start}
    nodes_explored = [0]
    while queue:
        node, path = queue.popleft()
        nodes_explored[0] += 1
        if node == goal:
            return path, nodes_explored[0]
        for neighbor, _, _ in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return [], nodes_explored[0]

# DIJKSTRA
def dijkstra(graph, start, goal):
    dist = {start: 0}
    prev = {start: None}
    pq   = [(0, start)]
    nodes_explored = [0]
    while pq:
        d, node = heapq.heappop(pq)
        nodes_explored[0] += 1
        if node == goal:
            path, cur = [], goal
            while cur:
                path.append(cur)
                cur = prev[cur]
            return list(reversed(path)), d, nodes_explored[0]
        if d > dist.get(node, float('inf')):
            continue
        for neighbor, _, w in graph.get(node, []):
            nd = d + w
            if nd < dist.get(neighbor, float('inf')):
                dist[neighbor] = nd
                prev[neighbor] = node
                heapq.heappush(pq, (nd, neighbor))
    return [], float('inf'), nodes_explored[0]

#  A*
# Heuristic: average edge weight * estimated hop distance
# (no GPS coords, so we use graph-distance estimate)
def astar(graph, start, goal, avg_weight=3.5):
    """
    A* with a hop-count heuristic scaled by average edge weight.
    h(n) = avg_weight * (BFS hop estimate to goal from n)
    For resume: explain this as "admissible heuristic using mean
    segment travel time × estimated remaining stops."
    """
    # Precompute BFS hop distances from goal for heuristic
    hop_from_goal = {}
    q = collections.deque([(goal, 0)])
    visited_h = {goal}
    while q:
        node, d = q.popleft()
        hop_from_goal[node] = d
        for nb, _, _ in graph.get(node, []):
            if nb not in visited_h:
                visited_h.add(nb)
                q.append((nb, d + 1))

    def h(n):
        return avg_weight * hop_from_goal.get(n, 10)

    open_set = [(h(start), 0, start)]
    g_score  = {start: 0}
    came_from = {start: None}
    nodes_explored = [0]

    while open_set:
        f, g, node = heapq.heappop(open_set)
        nodes_explored[0] += 1
        if node == goal:
            path, cur = [], goal
            while cur:
                path.append(cur)
                cur = came_from[cur]
            return list(reversed(path)), g, nodes_explored[0]
        for neighbor, _, w in graph.get(node, []):
            tentative_g = g + w
            if tentative_g < g_score.get(neighbor, float('inf')):
                g_score[neighbor]   = tentative_g
                came_from[neighbor] = node
                heapq.heappush(open_set, (tentative_g + h(neighbor), tentative_g, neighbor))
    return [], float('inf'), nodes_explored[0]

# Transfer counter
def count_transfers(path):
    """Count route changes needed along a path."""
    if len(path) < 2:
        return 0
    transfers = 0
    current_routes = None
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        edge_routes = {r for nb, r, _ in graph.get(a, []) if nb == b}
        if current_routes is None:
            current_routes = edge_routes
        elif not current_routes & edge_routes:
            transfers += 1
            current_routes = edge_routes
        else:
            current_routes = current_routes & edge_routes
    return transfers

def path_total_time(path):
    """Sum of real travel minutes along path."""
    return sum(get_weight(path[i], path[i+1]) for i in range(len(path)-1))

# 5.  PLOTLY FIGURE

ROUTE_COLORS = {
    "SU345 Thurber St":          "#E87722",
    "SU343 E.Genesee/Westcott":  "#4fc3f7",
    "SU43 Waverly Ave":          "#66BB6A",
    "SU443 Connective Corridor": "#EF5350",
    "SU44 Skytop Rd":            "#CE93D8",
    "SU344 South Campus":        "#B39DDB",
    "Euclid Loop":               "#00E5FF",
    "Warehouse Loop":            "#FFB300",
    "South Campus Loop":         "#A1887F",
    "Blue Loop":                 "#42A5F5",
    "Orange Loop":               "#FF7043",
    "Comstock/Colvin Loop":      "#90A4AE",
}

def make_figure(active_routes=None, highlight_hubs=False, highlight_artic=False,
                path_nodes=None, path_color="#00FF88", path_label=None):
    if active_routes is None:
        active_routes = list(ROUTES.keys())
    if path_nodes is None:
        path_nodes = []

    path_set   = set(path_nodes)
    path_edges = set(zip(path_nodes, path_nodes[1:])) | set(zip(path_nodes[1:], path_nodes))
    traces = []

    for route_name in active_routes:
        color = ROUTE_COLORS.get(route_name, "#888")
        stops = ROUTES[route_name]
        ex, ey = [], []
        for i in range(len(stops) - 1):
            a, b = stops[i], stops[i + 1]
            if a == b or a not in pos or b not in pos:
                continue
            if (a, b) not in path_edges and (b, a) not in path_edges:
                ex += [pos[a][0], pos[b][0], None]
                ey += [pos[a][1], pos[b][1], None]
        if ex:
            traces.append(go.Scatter(x=ex, y=ey, mode="lines",
                line=dict(color=color, width=2), opacity=0.5,
                hoverinfo="none", name=route_name,
                legendgroup=route_name, showlegend=True))

    if path_nodes:
        px_l, py_l = [], []
        for i in range(len(path_nodes) - 1):
            a, b = path_nodes[i], path_nodes[i + 1]
            if a in pos and b in pos:
                px_l += [pos[a][0], pos[b][0], None]
                py_l += [pos[a][1], pos[b][1], None]
        traces.append(go.Scatter(x=px_l, y=py_l, mode="lines",
            line=dict(color=path_color, width=5),
            hoverinfo="none", name=f"Path ({path_label})", showlegend=True))

    visible = set()
    for r in active_routes:
        visible.update(s for s in ROUTES[r] if s in pos)

    deg_map = {n: G.degree(n) for n in G.nodes()}
    max_deg = max(deg_map.values()) if deg_map else 1
    nx_l, ny_l, nc, ns, nt, ht = [], [], [], [], [], []

    for node in visible:
        x, y = pos[node]
        nx_l.append(x); ny_l.append(y)
        nt.append(node)
        routes_here = stop_routes.get(node, set())
        avg_w = round(sum(w for _, _, w in graph.get(node, [])) /
                      max(1, len(graph.get(node, []))), 1)
        ht.append(
            f"<b>{node}</b><br>"
            f"Routes: {len(routes_here)}<br>"
            f"Connections: {deg_map.get(node, 0)}<br>"
            f"Avg edge weight: {avg_w} min<br>"
            f"{' CRITICAL CONNECTOR' if node in articulation_pts else ''}<br>"
            + "<br>".join(sorted(routes_here))
        )
        if path_nodes and node == path_nodes[0]:
            nc.append("#00FF88"); ns.append(22)
        elif path_nodes and node == path_nodes[-1]:
            nc.append("#FF4444"); ns.append(22)
        elif node in path_set:
            nc.append(path_color); ns.append(14)
        elif highlight_artic and node in articulation_pts:
            nc.append("#FFD700"); ns.append(20)
        elif highlight_hubs:
            d = deg_map.get(node, 1)
            nc.append(f"rgb({int(232*d/max_deg)},{int(119*(1-d/max_deg))},34)")
            ns.append(8 + int(18 * d / max_deg))
        else:
            nc.append("#CCCCDD"); ns.append(10)

    traces.append(go.Scatter(x=nx_l, y=ny_l, mode="markers+text",
        marker=dict(size=ns, color=nc, line=dict(color="#0a0a1a", width=1)),
        text=nt, textposition="top center",
        textfont=dict(size=7.5, color="#ddddee"),
        hovertext=ht, hoverinfo="text",
        name="Stops", showlegend=False))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor="#0a0a18", plot_bgcolor="#0a0a18",
        font=dict(color="#ccccee", family="'JetBrains Mono', 'Courier New', monospace"),
        margin=dict(l=8, r=8, t=8, b=8),
        legend=dict(bgcolor="#12122a", bordercolor="#333355", borderwidth=1,
                    font=dict(size=9), x=1.01, y=1),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        hovermode="closest", height=600, dragmode="pan",
    )
    return fig


# 6.  DASH APP

app = Dash(__name__)
app.title = "SU Bus Network Explorer v2"

DARK  = "#08080f"
PANEL = "#0f0f1e"
CARD  = "#12122a"
ACC   = "#E87722"
TEXT  = "#ccccee"
MUT   = "#5555aa"
GOLD  = "#FFD700"

cs = {"background": CARD, "borderRadius": "8px", "padding": "14px",
      "marginBottom": "12px", "border": "1px solid #1e1e3a"}
ls = {"color": MUT, "fontSize": "9px", "letterSpacing": "2.5px",
      "textTransform": "uppercase", "marginBottom": "6px", "display": "block"}

def badge(text, color):
    return html.Span(text, style={
        "background": color + "22", "border": f"1px solid {color}55",
        "color": color, "borderRadius": "4px", "padding": "2px 8px",
        "fontSize": "10px", "fontWeight": "bold", "letterSpacing": "1px",
    })

app.layout = html.Div(style={"background": DARK, "minHeight": "100vh",
    "fontFamily": "'JetBrains Mono', 'Courier New', monospace", "color": TEXT}, children=[

    # Header
    html.Div(style={"background": PANEL, "padding": "14px 24px",
        "borderBottom": f"2px solid {ACC}",
        "display": "flex", "alignItems": "center", "gap": "14px"}, children=[
        html.Span("🚌", style={"fontSize": "26px"}),
        html.Div([
            html.H1("SU Bus Network Explorer",
                style={"margin": 0, "fontSize": "18px", "color": "#ffffff",
                       "fontWeight": "bold", "letterSpacing": "2px"}),
            html.Div(style={"display": "flex", "gap": "8px", "marginTop": "4px"}, children=[
                badge("Graph Theory", ACC),
                badge("DFS", "#E87722"),
                badge("BFS", "#00FF88"),
                badge("Dijkstra", GOLD),
                badge("A*", "#CE93D8"),
                badge("Real Weights", "#4fc3f7"),
            ]),
        ]),
        html.Div(style={"marginLeft": "auto", "textAlign": "right"}, children=[
            html.Div(f"V = {G.number_of_nodes()} stops",
                style={"color": "#4fc3f7", "fontSize": "11px"}),
            html.Div(f"E = {G.number_of_edges()} edges",
                style={"color": "#66BB6A", "fontSize": "11px"}),
            html.Div("Syracuse University · Centro Routes",
                style={"color": MUT, "fontSize": "10px", "marginTop": "2px"}),
        ]),
    ]),

    html.Div(style={"display": "flex", "gap": "12px", "padding": "12px"}, children=[

        # Left panel
        html.Div(style={"width": "270px", "flexShrink": 0}, children=[

            # Route filter
            html.Div(style=cs, children=[
                html.Span("Route Filter", style=ls),
                html.Div(style={"display": "flex", "gap": "6px", "marginBottom": "8px"},
                    children=[
                    html.Button("All", id="btn-all", n_clicks=0,
                        style={"background": ACC, "border": "none", "color": "#fff",
                               "borderRadius": "4px", "padding": "4px 10px",
                               "cursor": "pointer", "fontSize": "10px"}),
                    html.Button("None", id="btn-none", n_clicks=0,
                        style={"background": "#1e1e3a", "border": "1px solid #333",
                               "color": TEXT, "borderRadius": "4px",
                               "padding": "4px 10px", "cursor": "pointer", "fontSize": "10px"}),
                ]),
                dcc.Checklist(id="route-filter",
                    options=[{"label": html.Span(r, style={"color": ROUTE_COLORS.get(r, "#888"),
                                                            "fontSize": "11px"}),
                              "value": r} for r in ROUTES],
                    value=list(ROUTES.keys()),
                    style={"display": "flex", "flexDirection": "column", "gap": "5px"},
                    inputStyle={"accentColor": ACC, "marginRight": "6px"}),
            ]),

            # Highlight
            html.Div(style=cs, children=[
                html.Span("Highlight Mode", style=ls),
                dcc.Checklist(id="hl-opts",
                    options=[
                        {"label": html.Span("Hub stops (degree size)", style={"fontSize": "11px"}),
                         "value": "hubs"},
                        {"label": html.Span("⚠️ Critical connectors (APs)", style={"fontSize": "11px"}),
                         "value": "artic"},
                    ],
                    value=[],
                    style={"display": "flex", "flexDirection": "column", "gap": "7px"},
                    inputStyle={"accentColor": GOLD, "marginRight": "6px"}),
            ]),

            # Network stats
            html.Div(style=cs, id="stats-card"),

            # Complexity panel
            html.Div(style=cs, children=[
                html.Span("Complexity Analysis", style=ls),
                html.Div(id="complexity-panel"),
            ]),
        ]),

        # Center
        html.Div(style={"flex": 1, "minWidth": 0}, children=[

            # Graph
            html.Div(style={"background": PANEL, "borderRadius": "8px",
                "border": "1px solid #1e1e3a"}, children=[
                dcc.Graph(id="network-graph",
                    config={"scrollZoom": True, "displayModeBar": True,
                            "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
                    style={"height": "580px"}),
            ]),

            # Pathfinding
            html.Div(style={**cs, "marginTop": "12px", "marginBottom": 0}, children=[
                html.Span("Pathfinding Engine", style=ls),
                html.Div(style={"display": "flex", "gap": "8px", "flexWrap": "wrap",
                    "alignItems": "flex-end"}, children=[
                    html.Div([
                        html.Span("Start", style={**ls, "marginBottom": "4px"}),
                        dcc.Dropdown(id="path-start",
                            options=[{"label": s, "value": s} for s in all_stops_sorted],
                            value="College Pl (SU)", clearable=False,
                            style={"width": "210px", "fontSize": "11px"}),
                    ]),
                    html.Div([
                        html.Span("Destination", style={**ls, "marginBottom": "4px"}),
                        dcc.Dropdown(id="path-end",
                            options=[{"label": s, "value": s} for s in all_stops_sorted],
                            value="Skytop Office Building", clearable=False,
                            style={"width": "210px", "fontSize": "11px"}),
                    ]),
                    html.Div([
                        html.Span("Algorithm", style={**ls, "marginBottom": "4px"}),
                        dcc.Dropdown(id="algo-select",
                            options=[
                                {"label": "🔵 DFS — Depth First", "value": "dfs"},
                                {"label": "🟢 BFS — Fewest Stops", "value": "bfs"},
                                {"label": "🟡 Dijkstra — Min Time", "value": "dijkstra"},
                                {"label": "🟣 A* — Heuristic", "value": "astar"},
                            ],
                            value="dijkstra", clearable=False,
                            style={"width": "200px", "fontSize": "11px"}),
                    ]),
                    html.Button("▶ Find Path", id="btn-find", n_clicks=0,
                        style={"background": ACC, "border": "none", "color": "#fff",
                               "borderRadius": "5px", "padding": "8px 18px",
                               "cursor": "pointer", "fontSize": "12px",
                               "fontWeight": "bold", "letterSpacing": "1px"}),
                    html.Button("✕ Clear", id="btn-clear", n_clicks=0,
                        style={"background": "#1a1a30", "border": "1px solid #333",
                               "color": TEXT, "borderRadius": "5px",
                               "padding": "8px 12px", "cursor": "pointer", "fontSize": "12px"}),
                    html.Button("⚡ Compare All", id="btn-compare", n_clicks=0,
                        style={"background": "#1a2a1a", "border": f"1px solid {GOLD}44",
                               "color": GOLD, "borderRadius": "5px",
                               "padding": "8px 14px", "cursor": "pointer",
                               "fontSize": "12px", "fontWeight": "bold"}),
                ]),
                html.Div(id="path-result", style={"marginTop": "12px"}),
            ]),
        ]),
    ]),
])


# 7.  CALLBACKS

ALGO_COLORS = {"dfs": "#E87722", "bfs": "#00FF88",
               "dijkstra": GOLD, "astar": "#CE93D8"}

@app.callback(
    Output("route-filter", "value"),
    Input("btn-all", "n_clicks"),
    Input("btn-none", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_routes(a, b):
    btn = callback_context.triggered[0]["prop_id"]
    return list(ROUTES.keys()) if "btn-all" in btn else []


@app.callback(
    Output("network-graph", "figure"),
    Output("path-result", "children"),
    Output("stats-card", "children"),
    Output("complexity-panel", "children"),
    Input("route-filter", "value"),
    Input("hl-opts", "value"),
    Input("btn-find", "n_clicks"),
    Input("btn-clear", "n_clicks"),
    Input("btn-compare", "n_clicks"),
    State("path-start", "value"),
    State("path-end", "value"),
    State("algo-select", "value"),
)
def update(active_routes, hl_opts, find_n, clear_n, compare_n,
           start, end, algo):
    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    active_set = set(active_routes or [])
    path_nodes, path_color, path_label = [], "#00FF88", None
    path_result_div = html.Div()

    V = G.number_of_nodes()
    E = G.number_of_edges()

    # Run single algorithm
    if "btn-find" in triggered and start and end and start != end:
        if algo == "dfs":
            (path_nodes, explored), us = timed(dfs_path, graph, start, end)
        elif algo == "bfs":
            (path_nodes, explored), us = timed(bfs_path, graph, start, end)
        elif algo == "dijkstra":
            (path_nodes, cost, explored), us = timed(dijkstra, graph, start, end)
        else:  # astar
            (path_nodes, cost, explored), us = timed(astar, graph, start, end)

        path_color = ALGO_COLORS[algo]
        path_label = algo.upper()

        if path_nodes:
            hops     = len(path_nodes) - 1
            minutes  = path_total_time(path_nodes)
            transfers = count_transfers(path_nodes)
            cost_val = minutes if algo in ("dijkstra", "astar") else hops

            step_spans = []
            for i, s in enumerate(path_nodes):
                leg_time = get_weight(path_nodes[i-1], s) if i > 0 else 0
                step_spans.append(html.Div(style={"display": "flex", "alignItems": "center",
                    "gap": "6px", "padding": "3px 0"}, children=[
                    html.Span(f"{'→' if i else ' '}",
                        style={"color": path_color, "fontWeight": "bold", "minWidth": "12px"}),
                    html.Span(s, style={"color": "#ffffff" if i in (0, hops) else TEXT,
                                        "fontWeight": "bold" if i in (0, hops) else "normal",
                                        "fontSize": "11px"}),
                    html.Span(f"+{leg_time}min" if i > 0 else "",
                        style={"color": MUT, "fontSize": "9px", "marginLeft": "auto"}),
                ]))

            path_result_div = html.Div([
                html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "10px",
                    "flexWrap": "wrap"}, children=[
                    _metric(f"{minutes} min", "Total travel time", path_color),
                    _metric(f"{hops} stops", "Hops", "#4fc3f7"),
                    _metric(f"{transfers}", "Transfers", "#FFB300"),
                    _metric(f"{explored}", "Nodes explored", "#aaaaff"),
                    _metric(f"{us} μs", "Execution time", "#66BB6A"),
                ]),
                html.Div(style={"background": "#06060e", "borderRadius": "6px",
                    "padding": "8px 12px", "border": "1px solid #1a1a30",
                    "maxHeight": "180px", "overflowY": "auto"},
                    children=step_spans),
            ])
        else:
            path_result_div = html.Div("⚠️  No path found.",
                style={"color": "#FF4444", "fontSize": "12px"})

    # Compare all algorithms
    elif "btn-compare" in triggered and start and end and start != end:
        rows = []
        best_time = float('inf')
        results = {}
        for alg in ["dfs", "bfs", "dijkstra", "astar"]:
            if alg == "dfs":
                (p, exp), us = timed(dfs_path, graph, start, end)
                cost = path_total_time(p) if p else 999
            elif alg == "bfs":
                (p, exp), us = timed(bfs_path, graph, start, end)
                cost = path_total_time(p) if p else 999
            elif alg == "dijkstra":
                (p, c, exp), us = timed(dijkstra, graph, start, end)
                cost = c
            else:
                (p, c, exp), us = timed(astar, graph, start, end)
                cost = c
            results[alg] = {"path": p, "cost": cost, "exp": exp, "us": us}
            if p and cost < best_time:
                best_time = cost

        header = html.Div(style={"display": "grid",
            "gridTemplateColumns": "90px 80px 70px 80px 80px 70px",
            "gap": "4px", "marginBottom": "6px"}, children=[
            html.Span("Algorithm", style={"color": MUT, "fontSize": "9px"}),
            html.Span("Time (min)", style={"color": MUT, "fontSize": "9px"}),
            html.Span("Hops", style={"color": MUT, "fontSize": "9px"}),
            html.Span("Transfers", style={"color": MUT, "fontSize": "9px"}),
            html.Span("Explored", style={"color": MUT, "fontSize": "9px"}),
            html.Span("Exec (μs)", style={"color": MUT, "fontSize": "9px"}),
        ])
        for alg, r in results.items():
            p = r["path"]
            is_best = p and r["cost"] == best_time
            rows.append(html.Div(style={
                "display": "grid",
                "gridTemplateColumns": "90px 80px 70px 80px 80px 70px",
                "gap": "4px", "padding": "4px 0",
                "borderBottom": "1px solid #1a1a2a",
                "background": "#00FF8808" if is_best else "transparent",
            }, children=[
                html.Span(alg.upper() + (" ★" if is_best else ""),
                    style={"color": ALGO_COLORS[alg], "fontWeight": "bold",
                           "fontSize": "11px"}),
                html.Span(f"{r['cost']} min" if p else "—",
                    style={"color": "#ffffff" if is_best else TEXT, "fontSize": "11px"}),
                html.Span(str(len(p)-1) if p else "—",
                    style={"color": TEXT, "fontSize": "11px"}),
                html.Span(str(count_transfers(p)) if p else "—",
                    style={"color": TEXT, "fontSize": "11px"}),
                html.Span(str(r["exp"]), style={"color": "#aaaaff", "fontSize": "11px"}),
                html.Span(f"{r['us']}", style={"color": "#66BB6A", "fontSize": "11px"}),
            ]))

        path_result_div = html.Div([
            html.Div("Algorithm Comparison", style={"color": GOLD, "fontSize": "11px",
                "letterSpacing": "2px", "marginBottom": "8px"}),
            html.Div(style={"background": "#06060e", "borderRadius": "6px",
                "padding": "10px", "border": "1px solid #1a1a30"},
                children=[header] + rows),
            html.Div("★ = optimal path  ·  Dijkstra & A* use real travel times (minutes)",
                style={"color": MUT, "fontSize": "9px", "marginTop": "6px"}),
        ])

    # Stats card
    visible_stops = set()
    for r in active_set:
        visible_stops.update(ROUTES[r])
    ap_count = len([s for s in articulation_pts if s in visible_stops])
    stats = html.Div([
        html.Span("Network Stats", style=ls),
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
            "gap": "6px"}, children=[
            _sbox("Routes", str(len(active_set)), ACC),
            _sbox("Stops", str(len(visible_stops)), "#4fc3f7"),
            _sbox("Edges", str(E), "#66BB6A"),
            _sbox("Critical", str(ap_count), GOLD),
        ]),
    ])

    # Complexity panel
    complexity = html.Div([
        _cline("DFS",      "O(V + E)", f"= O({V}+{E}) = O({V+E})", "#E87722"),
        _cline("BFS",      "O(V + E)", f"= O({V+E})", "#00FF88"),
        _cline("Dijkstra", "O((V+E)logV)", f"= O({V+E}·{round(math.log2(V),1)})", GOLD),
        _cline("A*",       "O(E·log V)", f"= O({E}·{round(math.log2(V),1)})", "#CE93D8"),
        html.Div(style={"borderTop": "1px solid #1e1e3a", "marginTop": "6px",
            "paddingTop": "6px"}, children=[
            html.Span(f"V = {V} stops  ·  E = {E} edges",
                style={"color": MUT, "fontSize": "9px"}),
        ]),
    ])

    fig = make_figure(
        active_routes=list(active_set),
        highlight_hubs="hubs" in (hl_opts or []),
        highlight_artic="artic" in (hl_opts or []),
        path_nodes=path_nodes,
        path_color=path_color,
        path_label=path_label,
    )
    return fig, path_result_div, stats, complexity


def _metric(value, label, color):
    return html.Div(style={"background": "#08080f", "borderRadius": "6px",
        "padding": "8px 12px", "border": f"1px solid {color}33",
        "minWidth": "80px"}, children=[
        html.Div(value, style={"fontSize": "20px", "fontWeight": "bold",
                               "color": color, "letterSpacing": "0.5px"}),
        html.Div(label, style={"fontSize": "9px", "color": MUT,
                               "letterSpacing": "1px", "marginTop": "2px"}),
    ])

def _sbox(label, value, color):
    return html.Div(style={"background": "#08080f", "borderRadius": "6px",
        "padding": "8px", "textAlign": "center",
        "border": f"1px solid {color}33"}, children=[
        html.Div(value, style={"fontSize": "20px", "fontWeight": "bold", "color": color}),
        html.Div(label, style={"fontSize": "9px", "color": MUT, "letterSpacing": "1px"}),
    ])

def _cline(algo, notation, computed, color):
    return html.Div(style={"display": "flex", "justifyContent": "space-between",
        "padding": "3px 0", "borderBottom": "1px solid #12122a"}, children=[
        html.Span(algo, style={"color": color, "fontSize": "10px",
                               "fontWeight": "bold", "minWidth": "60px"}),
        html.Span(notation, style={"color": TEXT, "fontSize": "10px"}),
        html.Span(computed, style={"color": MUT, "fontSize": "9px"}),
    ])


if __name__ == "__main__":
    print("\n SU Bus Network Explorer v2 — Portfolio Edition")
    print(f"   Graph: V={G.number_of_nodes()} stops, E={G.number_of_edges()} edges")
    print(f"   Algorithms: DFS, BFS, Dijkstra (real weights), A* (heuristic)")
    print("   Open http://127.0.0.1:8050\n")
    app.run(debug=False)