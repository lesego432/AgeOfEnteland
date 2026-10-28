import heapq
import json
import os


def travel(destination: str, fast: bool = False) -> dict:
    action = {"type": "travel", "destination": destination}
    if fast:
        action["fast"] = True
    return action


def gather() -> dict:
    return {"type": "gather"}


def sell(item: str, quantity: int) -> dict:
    return {"type": "sell", "item": item, "quantity": quantity}


def buy(item: str, quantity: int) -> dict:
    return {"type": "buy", "item": item, "quantity": quantity}


def build_adjacency_list(routes: list) -> dict:
    graph = {}
    for route in routes:
        u, v = route["between"]
        weight = route["weight"]
        if route.get("toll", 0) == 0:
            graph.setdefault(u, []).append((v, weight))
            graph.setdefault(v, []).append((u, weight))
    return graph


def dijkstra(graph: dict, start: str):
    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    distances[start] = 0
    pq = [(0, start)]

    while pq:
        curr_dist, u = heapq.heappop(pq)
        if curr_dist > distances[u]:
            continue
        for neighbor, weight in graph.get(u, []):
            distance = curr_dist + weight
            if distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = distance
                previous[neighbor] = u
                heapq.heappush(pq, (distance, neighbor))
    return distances, previous


def get_shortest_path(previous: dict, start: str, target: str) -> list:
    path = []
    curr = target
    while curr != start:
        if curr is None:
            return []
        path.append(curr)
        curr = previous[curr]
    path.reverse()
    return path


def solve_level1(level_data: dict) -> list:
    run_info = level_data["run"]
    total_ticks = run_info["total_ticks"]
    current_town = run_info["starting_town"]

    nodes = level_data.get("nodes", {})
    towns = level_data.get("towns", {})
    routes = level_data.get("routes", [])

    graph = build_adjacency_list(routes)
    actions = []
    elapsed_ticks = 0
    current_pos = current_town

    raw_sell_prices = {
        "wheat": 2,
        "wood": 3,
        "stone": 3,
        "clay": 4,
        "fish": 4,
        "sheep": 5,
        "ore": 6,
    }

    best_node_id = None
    best_value_density = -1

    for node_id, node_info in nodes.items():
        res = node_info["resource"]
        yield_amount = node_info["yield"]
        gather_time = node_info["gather-time"]
        unit_price = raw_sell_prices.get(res, 1)

        value_per_tick = (yield_amount * unit_price) / gather_time
        if value_per_tick > best_value_density:
            best_value_density = value_per_tick
            best_node_id = node_id

    if not best_node_id:
        return actions

    _, prev_map = dijkstra(graph, current_pos)
    path_to_node = get_shortest_path(prev_map, current_pos, best_node_id)

    travel_ticks_to_node = 0
    curr = current_pos
    for step in path_to_node:
        for nxt, w in graph[curr]:
            if nxt == step:
                travel_ticks_to_node += w
                break
        curr = step

    for step in path_to_node:
        actions.append(travel(step))
    elapsed_ticks += travel_ticks_to_node
    current_pos = best_node_id

    distances_from_node, prev_from_node = dijkstra(graph, best_node_id)
    closest_town = min(
        towns.keys(), key=lambda t: distances_from_node.get(t, float("inf"))
    )
    travel_ticks_to_town = distances_from_node[closest_town]
    path_to_town = get_shortest_path(prev_from_node, best_node_id, closest_town)

    node_info = nodes[best_node_id]
    node_gather_time = node_info["gather-time"]
    node_yield = node_info["yield"]
    res_type = node_info["resource"]

    buffer_ticks = travel_ticks_to_town + 1
    available_gather_ticks = total_ticks - elapsed_ticks - buffer_ticks
    gather_count = max(0, available_gather_ticks // node_gather_time)

    for _ in range(gather_count):
        actions.append(gather())
        elapsed_ticks += node_gather_time

    for step in path_to_town:
        actions.append(travel(step))
    elapsed_ticks += travel_ticks_to_town

    total_gathered = gather_count * node_yield
    if total_gathered > 0:
        actions.append(sell(res_type, total_gathered))

    return actions


if __name__ == "__main__":
    level_file = "level1.json"

    if not os.path.exists(level_file) or os.path.getsize(level_file) == 0:
        sample_level = {
            "run": {
                "total_ticks": 500,
                "starting_town": "Demacia",
                "starting_enteloot": 200,
            },
            "towns": {
                "Demacia": {
                    "production": {"rate": 10, "resources": {"wheat": 2}},
                    "enteloot": {"rate": 5, "amount": 1000},
                },
                "Piltover": {
                    "production": {"rate": 10, "resources": {"fish": 2}},
                    "enteloot": {"rate": 2, "amount": 400},
                },
            },
            "nodes": {
                "N1": {
                    "type": "fields",
                    "resource": "wheat",
                    "yield": 6,
                    "gather-time": 2,
                }
            },
            "routes": [
                {"between": ["Demacia", "N1"], "weight": 2, "toll": 0},
                {"between": ["N1", "Piltover"], "weight": 3, "toll": 0},
            ],
        }
        with open(level_file, "w") as f:
            json.dump(sample_level, f, indent=2)

    with open(level_file, "r") as f:
        level_data = json.load(f)

    action_sequence = solve_level1(level_data)
    submission = {"actions": action_sequence}

    with open("level1_output.txt", "w") as f:
        json.dump(submission, f, indent=2)

    print("Successfully generated level1_output.txt!")