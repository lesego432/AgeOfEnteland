import json
import heapq
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))

possible_paths = [
    os.path.join(script_dir, "level2.json"),
    os.path.join(script_dir, "2.txt"),
    os.path.join(script_dir, "..", "level2.json"),
    r"C:\Users\Lesego\Downloads\level2.json"
]

file_path = None
for p in possible_paths:
    if os.path.isfile(p):
        file_path = p
        break

if not file_path:
    print("ERROR: Could not find level2.json or 2.txt")
    sys.exit(1)

print(f"Successfully loaded file from: {file_path}")

with open(file_path, "r") as f:
    data = json.load(f)

run_info = data["run"]
total_ticks = run_info["total_ticks"]
current_location = run_info["starting_town"]
enteloot = run_info["starting_enteloot"]

towns = data["towns"]
nodes = data["nodes"]
routes = data["routes"]

graph = {}
for loc in list(towns.keys()) + list(nodes.keys()):
    graph[loc] = []

for r in routes:
    u, v = r["between"]
    w = r["weight"]
    graph[u].append((v, w))
    graph[v].append((u, w))

def get_shortest_path(start, target):
    if start == target:
        return []
    queue = [(0, start, [])]
    visited = set()
    while queue:
        (cost, current, path) = heapq.heappop(queue)
        if current in visited:
            continue
        visited.add(current)
        if current == target:
            return path
        for neighbor, weight in graph[current]:
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
    return []

actions = []
current_tick = 0
inventory = {}

def execute_travel(dest):
    global current_location, current_tick
    if current_location == dest:
        return
    path = get_shortest_path(current_location, dest)
    for next_hop in path:
        for neighbor, weight in graph[current_location]:
            if neighbor == next_hop:
                if current_tick + weight > total_ticks:
                    return
                current_tick += weight
                actions.append({"type": "travel", "destination": next_hop})
                current_location = next_hop
                break

def execute_gather(count):
    global current_tick
    gather_time = nodes[current_location]["gather-time"]
    yield_qty = nodes[current_location]["yield"]
    res = nodes[current_location]["resource"]
    for _ in range(count):
        if current_tick + gather_time > total_ticks:
            break
        current_tick += gather_time
        actions.append({"type": "gather"})
        inventory[res] = inventory.get(res, 0) + yield_qty

recipes = {
    "planks": {"inputs": {"wood": 2}},
    "thatch": {"inputs": {"wheat": 2}},
    "stone-blocks": {"inputs": {"stone": 3}},
    "mortar": {"inputs": {"clay": 1, "stone": 1}},
    "bricks": {"inputs": {"clay": 2, "mortar": 1}},
    "rope": {"inputs": {"sheep": 2}},
    "fencing": {"inputs": {"wood": 2, "rope": 1}},
    "kiln-glass": {"inputs": {"clay": 2, "wood": 2}},
    "nets": {"inputs": {"rope": 1, "fencing": 1}},
    "stone-works": {"inputs": {"stone": 5}},
    "roof-tiles": {"inputs": {"clay": 3, "stone": 2}},
    "pottery": {"inputs": {"clay": 4, "wood": 1}},
    "bread": {"inputs": {"wheat": 3}}
}

upgrade_specs = {
    "farmhouse": {"build_time": 3, "enteloot_cost": 500, "components": {"planks": 3, "thatch": 2}},
    "pier": {"build_time": 3, "enteloot_cost": 600, "components": {"planks": 4, "nets": 2}},
    "fertilised-fields": {"build_time": 3, "enteloot_cost": 500, "components": {"fencing": 2, "thatch": 2}},
    "quarry": {"build_time": 3, "enteloot_cost": 600, "components": {"stone-blocks": 3, "planks": 2}},
    "woodlands": {"build_time": 3, "enteloot_cost": 500, "components": {"fencing": 2, "rope": 2}},
    "pottery-house": {"build_time": 3, "enteloot_cost": 700, "components": {"bricks": 4, "planks": 2}},
    "rec-center": {"build_time": 4, "enteloot_cost": 1200, "components": {"planks": 4, "bricks": 3, "rope": 1}},
    "fire-station": {"build_time": 4, "enteloot_cost": 1800, "components": {"bricks": 5, "stone-blocks": 3, "rope": 2}},
    "school": {"build_time": 5, "enteloot_cost": 2000, "components": {"bricks": 6, "planks": 3, "kiln-glass": 2}},
    "library": {"build_time": 5, "enteloot_cost": 2500, "components": {"bricks": 5, "planks": 5, "kiln-glass": 2}}
}

def execute_craft(item, qty):
    global current_tick
    affinity = "crafting" in towns.get(current_location, {}).get("affinities", [])
    time_per_item = 1 if affinity else 2
    total_time = qty * time_per_item
    if current_tick + total_time > total_ticks:
        return
    
    for ing, req_qty in recipes[item]["inputs"].items():
        if inventory.get(ing, 0) < req_qty * qty:
            return
        inventory[ing] -= req_qty * qty
        
    current_tick += total_time
    actions.append({"type": "craft", "item": item, "quantity": qty})
    inventory[item] = inventory.get(item, 0) + qty

def execute_sell(item, qty):
    global current_tick, enteloot
    if current_tick + 1 > total_ticks:
        return
    if inventory.get(item, 0) < qty:
        return
    current_tick += 1
    actions.append({"type": "sell", "item": item, "quantity": qty})
    price = towns[current_location]["item-rates"].get(item, 0)
    enteloot += price * qty
    inventory[item] -= qty

def execute_build(upgrade_name):
    global current_tick, enteloot
    spec = upgrade_specs[upgrade_name]
    build_time = spec["build_time"]
    cost = spec["enteloot_cost"]
    if current_tick + build_time > total_ticks or enteloot < cost:
        return
    
    for comp, qty in spec["components"].items():
        if inventory.get(comp, 0) < qty:
            return
        inventory[comp] -= qty
        
    enteloot -= cost
    current_tick += build_time
    actions.append({"type": "build", "upgrade": upgrade_name})

# Phase 1: Generate initial Enteloot currency
while enteloot < 120000 and current_tick < 2200:
    execute_travel("N2")
    execute_gather(30)
    execute_travel("Demacia")
    execute_craft("stone-works", 42)
    execute_sell("stone-works", 42)

    execute_travel("N7")
    execute_gather(30)
    execute_travel("Demacia")
    execute_travel("N2")
    execute_gather(15)
    execute_travel("Demacia")
    execute_craft("roof-tiles", 50)
    execute_sell("roof-tiles", 50)

# Phase 2: Construct town upgrades across the map
target_towns = list(towns.keys())
craft_plan = [
    ("planks", 32), ("thatch", 4), ("stone-blocks", 6), 
    ("mortar", 18), ("rope", 11), ("kiln-glass", 4), 
    ("bricks", 18), ("fencing", 4), ("nets", 2)
]

for town in target_towns:
    if current_tick >= total_ticks - 500:
        break

    execute_travel("N11")
    execute_gather(11)

    execute_travel("N5")
    execute_gather(2)

    execute_travel("N2")
    execute_gather(6)

    execute_travel("N7")
    execute_gather(16)

    execute_travel("N14")
    execute_gather(7)

    execute_travel("Demacia")

    for item, qty in craft_plan:
        execute_craft(item, qty)

    execute_travel(town)

    all_upgrades = ["farmhouse", "pier", "fertilised-fields", "quarry", "woodlands", "pottery-house", "rec-center", "fire-station", "school", "library"]
    for u in all_upgrades:
        execute_build(u)

output = {"actions": actions}
output_path = os.path.join(script_dir, "level2_output.txt")
with open(output_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Level 2 solution generated. Total Actions: {len(actions)}, Final Tick: {current_tick}")