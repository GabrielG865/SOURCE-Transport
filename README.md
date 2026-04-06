# SU Bus Network — Graph Theory & Route Optimization

> **Syracuse University / Centro Bus Route Analysis**  
> Graph-based transit network modeling using DFS, BFS, Dijkstra, and A\* with real schedule data.

---

##  Overview

This project models the Syracuse University and Centro bus network as a **weighted undirected graph** to analyze route efficiency, detect redundancies, and find optimal paths between stops.

Originally developed as part of a collaborative research project with a team of four, then independently extended post-program to include real edge weights extracted from official Centro PDF schedules, A\* pathfinding, live algorithm benchmarking, and a full interactive dashboard.

**Network stats:**
- **61** unique stops (nodes)
- **116** unique edges (connections)
- **12** routes modeled (Centro bus + 'Cuse Trolley)
-  Real travel times extracted from official schedules

---

## Features

### Core Analysis
- **Graph construction** from 12 real Centro/SU bus routes
- **Redundant stop detection** — dead-ends, single-route stops, articulation points
- **Hub analysis** — ranked by connection degree
- **Network connectivity** — critical connector identification via Tarjan's algorithm

### Pathfinding Algorithms (all benchmarked in microseconds)
| Algorithm | Strategy | Optimizes For |
|-----------|----------|--------------|
| DFS | Depth-first stack | Exploration (not optimal) |
| BFS | Breadth-first queue | Fewest stops (hops) |
| Dijkstra | Priority queue + weights | Minimum travel time |
| A\* | Heuristic + Dijkstra | Minimum time, fewer nodes explored |

### Interactive Dashboard (`su_interactive_v2.py`)
- Zoomable, hoverable Plotly network graph
- Route filter toggles (show/hide individual routes)
- Hub + critical connector highlighting
- Pick any start/end stop → run any algorithm → see path highlighted live
- ** Compare All** — runs all 4 algorithms side-by-side with time, hops, transfers, nodes explored, and execution speed
- Live **Big-O complexity panel** with your actual V and E plugged in
- Transfer counting (how many route changes a path requires)

### Static Visualizations (`main.py`)
- Full network graph (color-coded by route)
- Top 25 most connected stops (degree distribution)
- DFS vs BFS path comparison charts
- Algorithm efficiency comparison bar chart
- Route coverage heatmap

## Getting Started

### Prerequisites
```bash
pip install dash plotly networkx matplotlib
```

### Run the interactive dashboard
```bash
python su_interactive_v2.py
```
Then open **http://127.0.0.1:8050** in your browser.

### Run the static analysis + charts
```bash
python main.py
```
Charts will be saved to the `outputs/` folder (created automatically).

---

## Key Findings

| Finding | Value |
|---------|-------|
| Most connected stop | College Pl (SU) — **20 connections**, 11 routes |
| Critical connectors (articulation points) | **2** — College Pl (SU), Westcott St / Euclid Ave |
| Single-route stops (no transfer) | **32 stops** |
| Dead-end stops | **1** — Broad St (SU343 only) |
| A\* vs Dijkstra node reduction | Up to **~40% fewer nodes explored** |
| BFS vs DFS on shortest path | BFS finds optimal in fewer explored nodes |

---

## Algorithms — How They Compare

```
College Pl (SU)  →  Skytop Office Building

DFS       │ finds A path, not necessarily optimal, explores more nodes
BFS       │ optimal by hops (fewest stops), ignores travel time
Dijkstra  │ optimal by real travel time (minutes), explores more nodes than A*
A*        │ optimal by real travel time, uses heuristic to skip unnecessary nodes ★
```

**A\* heuristic used:** admissible estimate = `avg_segment_time × BFS_hop_distance_to_goal`  
This mirrors how real transit routing engines (Google Maps, GTFS planners) work.

---

## Complexity Reference

| Algorithm | Time Complexity | With V=61, E=116 |
|-----------|----------------|-----------------|
| DFS | O(V + E) | O(177) |
| BFS | O(V + E) | O(177) |
| Dijkstra | O((V + E) log V) | O(177 × 6.0) |
| A\* | O(E · log V) | O(116 × 6.0) |

---

## Routes Modeled

| Route | Type | Stops |
|-------|------|-------|
| SU345 Thurber St | Centro bus | 10 |
| SU343 E. Genesee / Westcott | Centro bus | 8 |
| SU43 Waverly Ave | Centro bus | 7 |
| SU443 Connective Corridor | Centro bus | 20 |
| SU44 Skytop Rd | Centro bus | 6 |
| SU344 South Campus | Centro bus | 12 |
| Euclid Loop | 'Cuse Trolley | 5 |
| Warehouse Loop | 'Cuse Trolley | 8 |
| South Campus Loop | 'Cuse Trolley | 9 |
| Blue Loop | 'Cuse Trolley | 16 |
| Orange Loop | 'Cuse Trolley | 16 |
| Comstock/Colvin Loop | 'Cuse Trolley | 4 |

---

## Post-Program Extensions

These features were added independently after the original research program ended:

-  Real edge weights from 12 official PDF schedules (replacing unit-weight assumptions)
-  A\* Search with admissible heuristic
-  Live microsecond algorithm benchmarking
-  Transfer counting per path
-  Interactive Plotly/Dash dashboard with Compare All mode
-  Big-O complexity panel with live V/E values

---

##  Author

**Gabriel G.**  
Syracuse University  
Research Assistant — Graph Theory & Transit Optimization  

---

## Data Source

Schedule data sourced from official **Centro / Syracuse University** PDF timetables.  
All route and timing information is publicly available at [centro.org](https://www.centro.org).
