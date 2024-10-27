import numpy as np
from typing import List, Tuple
from DA import DeliveryAgent, create_delivery_agents
from parcels import Package

def load_parcels_from_file(filename):
    parcels = []
    with open(filename, 'r') as f:
        next(f)  # To skip the header of file
        for line_num, line in enumerate(f, 2):
            try:
                parts = line.strip().split(',')
                if len(parts) >= 4:  # Making sure we have all parcel details
                    customer_id = parts[0].strip()
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    num_parcels = int(parts[3].strip())
                    parcels.append(Package(customer_id, (x, y), num_parcels))
                else:
                    print(f"Warning: Skipping invalid line {line_num}: {line.strip()}")
            except ValueError as e:
                print(f"Error parsing line {line_num}: {line.strip()}")
                print(f"Error details: {str(e)}")
    
    if not parcels:
        raise ValueError("No valid parcels found in the file.")
    
    return parcels

class MasterRoutingAgent:
    def __init__(self, depot_location: Tuple[float, float], num_agents: int, capacity_per_agent: int):
        self.depot_location = depot_location
        self.num_agents = num_agents
        self.capacity_per_agent = capacity_per_agent
        self.delivery_agents = None
        self.parcels = []
        self.distance_matrix = None
        self.max_distances = None

    def set_parcels(self, parcels: List[Package]):
        self.parcels = parcels
        self._precompute_distances()
        self._adjust_capacity()

    def _adjust_capacity(self):
        total_parcels = sum(parcel.num_parcels for parcel in self.parcels)
        total_capacity = self.num_agents * self.capacity_per_agent
        
        # Ensure total capacity is less than total parcels
        if total_capacity >= total_parcels:
            reduction_factor = 0.7  # Reduce capacity by 30%
            new_capacity = int((total_parcels * reduction_factor) / self.num_agents)
            self.capacity_per_agent = max(1, new_capacity)  # Ensure minimum capacity of 1
        
        self.delivery_agents = create_delivery_agents(self.num_agents, self.capacity_per_agent, None)

    def set_max_distances(self, max_distances: List[float]):
        if len(max_distances) != len(self.delivery_agents):
            raise ValueError("Number of max distances must match number of delivery agents")
        self.max_distances = max_distances
        for agent, max_distance in zip(self.delivery_agents, max_distances):
            agent.max_distance = max_distance

    def _precompute_distances(self):
        locations = [self.depot_location] + [p.destination for p in self.parcels]
        self.distance_matrix = np.array([[self.calculate_distance(p1, p2) for p2 in locations] for p1 in locations])

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    def optimize_deliveries(self):
        if self.max_distances is None:
            raise ValueError("Max distances not set. Call set_max_distances before optimizing.")

        unassigned_parcels = list(range(len(self.parcels)))
        routes = [[] for _ in self.delivery_agents]
        parcels_delivered = [[] for _ in self.delivery_agents]
        agent_loads = [0 for _ in self.delivery_agents]
        agent_distances = [0 for _ in self.delivery_agents]

        max_iterations = len(self.parcels) * len(self.delivery_agents) * 2
        iteration_count = 0

        while unassigned_parcels and iteration_count < max_iterations:
            iteration_count += 1
            for i, agent in enumerate(self.delivery_agents):
                if not unassigned_parcels:
                    break

                if not routes[i] or routes[i][-1] == -1:
                    routes[i].append(-1)  # Start from depot
                    parcels_delivered[i].append(0)  # No parcels delivered at depot

                current_location = self.depot_location if routes[i][-1] == -1 else self.parcels[routes[i][-1]].destination
                
                best_next = None
                best_score = float('-inf')
                for j in unassigned_parcels:
                    next_location = self.parcels[j].destination
                    distance_to_next = self.calculate_distance(current_location, next_location)
                    distance_to_depot = self.calculate_distance(next_location, self.depot_location)
                    total_distance = agent_distances[i] + distance_to_next + distance_to_depot

                    if total_distance <= agent.max_distance:
                        remaining_capacity = agent.capacity - agent_loads[i]
                        parcels_to_deliver = min(remaining_capacity, self.parcels[j].num_parcels)
                        score = parcels_to_deliver - (distance_to_next / 1000)  # Prioritize parcels over distance
                        if score > best_score:
                            best_next = j
                            best_score = score

                if best_next is None or agent_loads[i] >= agent.capacity:
                    # Return to depot
                    if routes[i][-1] != -1:
                        routes[i].append(-1)
                        parcels_delivered[i].append(0)  # No parcels delivered when returning to depot
                        agent_distances[i] += self.calculate_distance(current_location, self.depot_location)
                    agent_loads[i] = 0
                    continue

                routes[i].append(best_next)
                parcels_to_deliver = min(agent.capacity - agent_loads[i], self.parcels[best_next].num_parcels)
                parcels_delivered[i].append(parcels_to_deliver)
                agent_loads[i] += parcels_to_deliver
                agent_distances[i] += self.calculate_distance(current_location, self.parcels[best_next].destination)

                self.parcels[best_next].num_parcels -= parcels_to_deliver
                if self.parcels[best_next].num_parcels == 0:
                    unassigned_parcels.remove(best_next)

        # Ensure all routes end at the depot
        for i, route in enumerate(routes):
            if route[-1] != -1:
                routes[i].append(-1)
                parcels_delivered[i].append(0)
                agent_distances[i] += self.calculate_distance(self.parcels[route[-2]].destination, self.depot_location)

        return routes, parcels_delivered

    def calculate_route_costs(self, routes):
        costs = []
        total_distances = []
        for route in routes:
            cost = 0
            distance = 0
            current_location = 0  # Starting at the depot
            for stop in route:
                next_location = 0 if stop == -1 else stop + 1  # adding 1 as depot is at position 0
                leg_distance = self.distance_matrix[current_location][next_location]
                cost += leg_distance
                distance += leg_distance
                current_location = next_location
            costs.append(cost)
            total_distances.append(distance)
        return costs, total_distances

    def calculate_detailed_route_costs(self, routes, parcels_delivered):
        detailed_costs = []
        for route, parcels in zip(routes, parcels_delivered):
            route_details = []
            total_cost = 0
            current_location = 0
            for stop, num_parcels in zip(route, parcels):
                next_location = 0 if stop == -1 else stop + 1
                cost = self.distance_matrix[current_location][next_location]
                if cost > 0:  # Only add non-zero cost movements
                    if stop == -1:
                        route_details.append(("Return to Depot", cost, 0))
                    else:
                        route_details.append((f"Customer {self.parcels[stop].customer_id}", cost, num_parcels))
                    total_cost += cost
                current_location = next_location
            route_details.append(("Total", total_cost, sum(parcels)))
            detailed_costs.append(route_details)
        return detailed_costs

    def print_routes(self, routes):
        for i, route in enumerate(routes):
            print(f"Route for DA_{i + 1}:")
            for stop in route:
                if stop == -1:
                    print("  Return to Depot")
                else:
                    parcel = self.parcels[stop]
                    print(f"  Deliver {parcel.num_parcels} parcels to Customer {parcel.customer_id} at {parcel.destination}")
            print()