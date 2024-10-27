import random
class DeliveryAgent:
    def __init__(self, da_id, capacity, max_distance):
        self.da_id = da_id
        self.capacity = capacity
        self.max_distance = max_distance
        self.load = 0 #Load is 0 before a load is assigned (placeholder)
        self.route = []

    def get_capacity(self):
        return [random.randint(20, 50)]
    def get_max_Distance(DeliveryAgent):
        return DeliveryAgent.max_distance
    def set_max_distance(self, max_distance):
        self.max_distance= max_distance
    def get_route(self, route):
        self.route = route
        print(f"DA {self.da_id} received a new route with {len(route)} stops.")

    def deliver_parcels(self):
        delivered = 0
        for parcel in self.route:
            if self.load + parcel.num_parcels <= self.capacity:
                self.load += parcel.num_parcels
                print(f"DA {self.da_id} delivering {parcel.num_parcels} parcels to Customer {parcel.customer_id} at {parcel.destination}")
                delivered += parcel.num_parcels
            else:
                print(f"DA {self.da_id} at full capacity. Cannot deliver more parcels.")
                break
        return delivered

    def get_status(self):
        return {
            'DA ID': self.da_id,
            'Capacity': self.capacity,
            'Current Load': self.load
        }

# DA factory to make DAs as required
def create_delivery_agents(num_agents, capacity_per_agent, max_distance):
    agents = []
    for i in range(num_agents):
        da_id = f"DA_{i + 1}"
        da = DeliveryAgent(da_id=da_id, capacity=capacity_per_agent, max_distance=max_distance)
        agents.append(da)
    return agents