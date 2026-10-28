import json
import math
from collections import deque

def solve():
    input_file = "level4.json"
    output_file = "level4_output.txt"
    
    with open(input_file, "r") as f:
        data = json.load(f)
        
    print(f"Successfully loaded file from: {input_file}")

    # Robust Root-Level Key Resolution
    player_data = data.get("player", {})
    start_node = (
        player_data.get("location") or 
        data.get("start_node") or 
        data.get("player_location") or 
        data.get("start") or 
        (list(data.get("towns", {}).keys())[0] if data.get("towns") else "Demacia")
    )
    enteloot = player_data.get("enteloot", data.get("enteloot", data.get("starting_enteloot", 0)))
    total_ticks = (
        data.get("max_ticks") or 
        data.get("maxTicks") or 
        data.get("ticks") or 
        data.get("time_limit") or 
        2000
    )

    towns = data.get("towns", {})
    nodes = data.get("nodes", {})
    
    map_data = data.get("map", {})
    if isinstance(map_data, dict):
        graph_edges = map_data.get("edges", [])
    else:
        graph_edges = data.get("edges", [])
    
    # Build Adjacency Graph
    adj = {}
    for edge in graph_edges:
        u, v, w = edge["from"], edge["to"], edge["weight"]
        if u not in adj: adj[u] = []
        if v not in adj: adj[v] = []
        adj[u].append((v, w))
        adj[v].append((u, w))
        
    def get_shortest_path(start, target):
        if start == target:
            return []
        queue = deque([(start, [])])
        visited = {start}
        while queue:
            curr, path = queue.popleft()
            for neighbor, weight in adj.get(curr, []):
                if neighbor == target:
                    return path + [(neighbor, weight)]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [(neighbor, weight)]))
        return []

    actions = []
    current_tick = 0
    current_location = start_node
    inventory = {}
    has_boots = False
    has_pickaxe = False

    def execute_travel(target):
        nonlocal current_location, current_tick
        if current_location == target:
            return True
        path = get_shortest_path(current_location, target)
        for next_node, weight in path:
            cost = max(1, weight - 1) if has_boots else weight
            if current_tick + cost > total_ticks:
                return False
            current_tick += cost
            actions.append({"type": "travel", "destination": next_node})
            current_location = next_node
        return True

    def execute_gather(count, resource_name):
        nonlocal current_tick
        node_data = nodes.get(current_location, {})
        base_time = node_data.get("gather-time") or node_data.get("gather_time") or node_data.get("gatherTime", 2)
        yield_qty = node_data.get("yield", 1)
        eff_time = max(1, base_time - 1) if has_pickaxe else base_time
        
        for _ in range(count):
            if current_tick + eff_time > total_ticks:
                break
            current_tick += eff_time
            actions.append({"type": "gather"})
            inventory[resource_name] = inventory.get(resource_name, 0) + yield_qty

    def execute_craft(item, count=1):
        nonlocal current_tick, has_boots, has_pickaxe
        recipe = {
            "planks": {"inputs": {"wood": 2}},
            "thatch": {"inputs": {"wheat": 2}},
            "stone-blocks": {"inputs": {"stone": 3}},
            "mortar": {"inputs": {"clay": 1, "stone": 1}},
            "bricks": {"inputs": {"clay": 2, "mortar": 1}},
            "rope": {"inputs": {"sheep": 2}},
            "fencing": {"inputs": {"wood": 2, "rope": 1}},
            "kiln-glass": {"inputs": {"clay": 2, "wood": 2}},
            "nets": {"inputs": {"rope": 1, "fencing": 1}},
            "iron-fittings": {"inputs": {"ore": 2, "wood": 1}},
            "boots": {"inputs": {"iron-fittings": 2, "rope": 2}},
            "pickaxe": {"inputs": {"iron-fittings": 2, "planks": 2}},
            "roof-tiles": {"inputs": {"clay": 3, "stone": 2}}
        }[item]

        for _ in range(count):
            if current_tick + 1 > total_ticks:
                break
            for ing, req in recipe["inputs"].items():
                if inventory.get(ing, 0) < req:
                    return False
            for ing, req in recipe["inputs"].items():
                inventory[ing] -= req
            current_tick += 1
            actions.append({"type": "craft", "item": item, "quantity": 1})
            if item == "boots": has_boots = True
            elif item == "pickaxe": has_pickaxe = True
            else: inventory[item] = inventory.get(item, 0) + 1
        return True

    def execute_sell(item, count):
        nonlocal current_tick, enteloot
        prices = {"roof-tiles": 45, "bricks": 30, "stone-blocks": 25}
        price = prices.get(item, 20)
        for _ in range(count):
            if inventory.get(item, 0) <= 0 or current_tick + 1 > total_ticks:
                break
            inventory[item] -= 1
            enteloot += price
            current_tick += 1
            actions.append({"type": "sell", "item": item, "quantity": 1})

    def execute_build(upgrade):
        nonlocal current_tick, enteloot
        specs = {
            "farmhouse": {"cost": 500, "comps": {"planks": 3, "thatch": 2}},
            "pier": {"cost": 600, "comps": {"planks": 4, "nets": 2}},
            "fertilised-fields": {"cost": 500, "comps": {"fencing": 2, "thatch": 2}},
            "quarry": {"cost": 600, "comps": {"stone-blocks": 3, "planks": 2}},
            "woodlands": {"cost": 500, "comps": {"fencing": 2, "rope": 2}},
            "pottery-house": {"cost": 700, "comps": {"bricks": 4, "planks": 2}},
            "rec-center": {"cost": 1200, "comps": {"planks": 4, "bricks": 3, "rope": 1}},
            "fire-station": {"cost": 1800, "comps": {"bricks": 5, "stone-blocks": 3, "rope": 2}},
            "police-station": {"cost": 2200, "comps": {"bricks": 6, "stone-blocks": 4, "iron-fittings": 2}},
            "school": {"cost": 2000, "comps": {"bricks": 6, "planks": 3, "kiln-glass": 2}},
            "library": {"cost": 2500, "comps": {"bricks": 5, "planks": 5, "kiln-glass": 2}}
        }[upgrade]

        if enteloot < specs["cost"] or current_tick + 5 > total_ticks:
            return False
        for comp, qty in specs["comps"].items():
            if inventory.get(comp, 0) < qty:
                return False

        for comp, qty in specs["comps"].items():
            inventory[comp] -= qty
        enteloot -= specs["cost"]
        current_tick += 5
        actions.append({"type": "build", "upgrade": upgrade})
        return True

    def execute_upkeep():
        nonlocal current_tick
        if current_tick + 5 <= total_ticks:
            current_tick += 5
            actions.append({"type": "upkeep"})

    res_nodes = {}
    for nid, ndata in nodes.items():
        res = ndata.get("resource")
        if res and res not in res_nodes: 
            res_nodes[res] = nid

    craft_town = "Demacia" if "Demacia" in towns else list(towns.keys())[0]

    # PHASE 1: BOOTS & PICKAXE
    execute_travel(res_nodes["ore"])
    execute_gather(3, "ore")
    execute_travel(res_nodes["wood"])
    execute_gather(3, "wood")
    execute_travel(res_nodes["sheep"])
    execute_gather(2, "sheep")
    execute_travel(craft_town)
    execute_craft("iron-fittings", 4)
    execute_craft("rope", 2)
    execute_craft("planks", 2)
    execute_craft("boots", 1)
    execute_craft("pickaxe", 1)


    target_enteloot = len(towns) * 13100 + 5000
    while enteloot < target_enteloot and current_tick < 1500:
        execute_travel(res_nodes["clay"])
        execute_gather(12, "clay")
        execute_travel(res_nodes["stone"])
        execute_gather(10, "stone")
        execute_travel(craft_town)
        execute_craft("roof-tiles", 15)
        execute_sell("roof-tiles", 15)

    raw_per_town = {'wheat': 8, 'sheep': 26, 'stone': 59, 'clay': 95, 'wood': 68, 'ore': 4}
    num_towns = len(towns)
    
    execute_travel(res_nodes["wheat"])
    execute_gather(math.ceil((raw_per_town["wheat"] * num_towns) / nodes[res_nodes["wheat"]].get("yield", 1)), "wheat")
    execute_travel(res_nodes["sheep"])
    execute_gather(math.ceil((raw_per_town["sheep"] * num_towns) / nodes[res_nodes["sheep"]].get("yield", 1)), "sheep")
    execute_travel(res_nodes["ore"])
    execute_gather(math.ceil((raw_per_town["ore"] * num_towns) / nodes[res_nodes["ore"]].get("yield", 1)), "ore")
    execute_travel(res_nodes["stone"])
    execute_gather(math.ceil((raw_per_town["stone"] * num_towns) / nodes[res_nodes["stone"]].get("yield", 1)), "stone")
    execute_travel(res_nodes["clay"])
    execute_gather(math.ceil((raw_per_town["clay"] * num_towns) / nodes[res_nodes["clay"]].get("yield", 1)), "clay")
    execute_travel(res_nodes["wood"])
    execute_gather(math.ceil((raw_per_town["wood"] * num_towns) / nodes[res_nodes["wood"]].get("yield", 1)), "wood")

    execute_travel(craft_town)
    execute_craft("iron-fittings", 2 * num_towns)
    execute_craft("thatch", 4 * num_towns)
    execute_craft("stone-blocks", 10 * num_towns)
    execute_craft("mortar", 29 * num_towns)
    execute_craft("bricks", 29 * num_towns)
    execute_craft("rope", 13 * num_towns)
    execute_craft("fencing", 6 * num_towns)
    execute_craft("nets", 2 * num_towns)
    execute_craft("kiln-glass", 4 * num_towns)
    execute_craft("planks", 23 * num_towns)

    all_upgrades = [
        "farmhouse", "pier", "fertilised-fields", "quarry", "woodlands",
        "pottery-house", "rec-center", "fire-station", "police-station",
        "school", "library"
    ]
    for town in towns.keys():
        execute_travel(town)
        for up in all_upgrades:
            execute_build(up)
        execute_upkeep()

    town_list = list(towns.keys())
    while current_tick + 10 < total_ticks:
        for t in town_list:
            if current_tick + 15 >= total_ticks:
                break
            execute_travel(t)
            execute_upkeep()

    with open(output_file, "w") as f:
        json.dump({"actions": actions}, f, indent=2)

    print(f"Level 4 solution generated. Total Actions: {len(actions)}, Final Tick: {current_tick}")

if __name__ == "__main__":
    solve()