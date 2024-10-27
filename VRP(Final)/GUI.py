import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List
from MRA import MasterRoutingAgent, load_parcels_from_file
from CartesianPlane import generate_random_points
from parcels import Package
import threading
import random
from DA import DeliveryAgent

class CVRPGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("CVRP Route Planner")
        self.master.geometry("1200x800")  # Increased window size

        self.points = []
        self.depot = (0, 0)
        self.mra = None
        self.num_agents = 2
        self.num_points = 5
        self.capacity_per_agent = 10
        self.parcels = None
        self.routes = None
        self.parcels_delivered = None
        self.is_generating_routes = False
        self.route_generation_job = None

        self.create_widgets()

    def create_widgets(self):
        self.frame = ttk.Frame(self.master, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Creating input panel
        self.left_panel = ttk.Frame(self.frame)
        self.left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Input fields for the input panel
        self.input_frame = ttk.Frame(self.left_panel)
        self.input_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        ttk.Label(self.input_frame, text="Number of Points:").grid(row=0, column=0, padx=5, pady=5)
        self.num_points_entry = ttk.Entry(self.input_frame, width=5)
        self.num_points_entry.insert(0, str(self.num_points))
        self.num_points_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.input_frame, text="Number of DAs:").grid(row=0, column=2, padx=5, pady=5)
        self.num_agents_entry = ttk.Entry(self.input_frame, width=5)
        self.num_agents_entry.insert(0, str(self.num_agents))
        self.num_agents_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(self.input_frame, text="Max Distance:").grid(row=0, column=6, padx=5, pady=5)
        self.max_distance_entry = ttk.Entry(self.input_frame, width=5)
        self.max_distance_entry.insert(0, "200")  # Default max distance
        self.max_distance_entry.grid(row=0, column=7, padx=5, pady=5)

        ttk.Label(self.input_frame, text="Min Distance:").grid(row=0, column=4, padx=5, pady=5)
        self.min_distance_entry = ttk.Entry(self.input_frame, width=5)
        self.min_distance_entry.insert(0, "0")  # Default min distance
        self.min_distance_entry.grid(row=0, column=5, padx=5, pady=5)

        self.generate_btn = ttk.Button(self.left_panel, text="Generate Locations", command=self.generate_locations)
        self.generate_btn.grid(row=1, column=0, padx=5, pady=5)

        self.route_btn = ttk.Button(self.left_panel, text="Generate Route", command=self.generate_route)
        self.route_btn.grid(row=1, column=1, padx=5, pady=5)

        # Creating canvas with increased size
        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left_panel)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        # Creating a place to indicate path costs and routing details
        self.right_panel = ttk.Frame(self.frame)
        self.right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.cost_label = ttk.Label(self.right_panel, text="Path Costs:")
        self.cost_label.grid(row=0, column=0, padx=5, pady=5)

        self.cost_text = tk.Text(self.right_panel, width=40, height=30)  # Increased size
        self.cost_text.grid(row=1, column=0, padx=5, pady=5)

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # New label for parcel count
        self.parcel_count_label = ttk.Label(self.left_panel, text="")
        self.parcel_count_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def generate_locations(self):
        try:
            self.num_points = int(self.num_points_entry.get())
            self.num_agents = int(self.num_agents_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for points and DAs.")
            return

        self.ax.clear()
        self.points = generate_random_points(self.num_points, 0, 100, 0, 100)
        self.depot = generate_random_points(1, 0, 100, 0, 100)[0]

        x, y = zip(*self.points)
        self.ax.scatter(x, y, color='blue', label='Customers')
        self.ax.scatter(self.depot[0], self.depot[1], color='red', label='Depot')

        # Label customer locations
        for i, (x, y) in enumerate(self.points):
            self.ax.annotate(f'C{i+1}', (x, y), xytext=(5, 5), textcoords='offset points')

        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.legend()
        self.ax.set_title("Customer and Depot Locations")
        self.canvas.draw()

        # Create parcels file to store parcels data
        self.generate_parcels_file()
        self.status_label.config(text="Locations generated and parcels file created.")

    def generate_parcels_file(self):
        self.parcels = Package.create_parcels(self.num_points, self.points)
        Package.save_packages(self.parcels, "parcel_info.txt")
        self.update_parcel_count()

    def update_parcel_count(self):
        if self.parcels:
            total_parcels = sum(parcel.num_parcels for parcel in self.parcels)
            self.parcel_count_label.config(text=f"Total Parcels: {total_parcels}")

    def generate_random_vehicle_distances(self):
        try:
            min_distance = float(self.min_distance_entry.get())
            max_distance = float(self.max_distance_entry.get())
            if min_distance > max_distance:
                raise ValueError("Min distance cannot be greater than max distance.")
            return [random.uniform(min_distance, max_distance) for _ in range(self.num_agents)]
        except ValueError as e:
            messagebox.showerror("Input Error", f"Error: {str(e)}")
            return []

    def generate_route(self):
        if not self.points:
            self.status_label.config(text="Please generate locations first.")
            return

        if self.is_generating_routes:
            self.status_label.config(text="Route generation already in progress.")
            return

        self.status_label.config(text="Generating routes...")
        self.master.update()

        self.is_generating_routes = True
        threading.Thread(target=self.generate_route_thread, daemon=True).start()
        self.route_generation_job = self.master.after(100, self.check_route_progress)

    def generate_route_thread(self):
        try:
            self.mra = MasterRoutingAgent(self.depot, self.num_agents, self.capacity_per_agent)
            parcels = load_parcels_from_file('parcel_info.txt')
            self.mra.set_parcels(parcels)
            max_distances = self.generate_random_vehicle_distances()
            if not max_distances:
                raise ValueError("Failed to generate valid max distances.")
            self.mra.set_max_distances(max_distances)
            print("Generated Max Distances for Vehicles:", max_distances)
            self.routes, self.parcels_delivered = self.mra.optimize_deliveries()
        except ValueError as e:
            self.error_message = str(e)
            self.routes = None
        except Exception as e:
            self.error_message = f"Error generating routes: {str(e)}"
            self.routes = None
        finally:
            self.is_generating_routes = False

    def check_route_progress(self):
        if self.is_generating_routes:
            self.route_generation_job = self.master.after(100, self.check_route_progress)
        else:
            self.update_gui_with_routes()

    def update_gui_with_routes(self):
        if self.route_generation_job:
            self.master.after_cancel(self.route_generation_job)
            self.route_generation_job = None
        
        if self.routes:
            self.plot_routes(self.routes)
            self.update_path_costs()
            self.status_label.config(text="Route generation complete.")
        else:
            error_msg = getattr(self, 'error_message', "Route generation failed.")
            self.status_label.config(text=error_msg)
            messagebox.showerror("Error", error_msg)
            if "Unable to find a feasible solution" in error_msg:
                self.status_label.config(text="Vehicles cannot make the distance. Try increasing max distance or number of DAs.")

    def plot_routes(self, routes: List[List[int]]):
        self.ax.clear()

        # Plot the points on the cartesian plane
        x, y = zip(*self.points)
        self.ax.scatter(x, y, color='blue', label='Customers')
        self.ax.scatter(self.depot[0], self.depot[1], color='red', label='Depot', s=100)

        # Label customer locations
        for i, (x, y) in enumerate(self.points):
            self.ax.annotate(f'C{i+1}', (x, y), xytext=(5, 5), textcoords='offset points')

        # Show routes once generated
        colors = ['g', 'm', 'c', 'y', 'k']
        for i, route in enumerate(routes):
            color = colors[i % len(colors)]
            route_points = [self.depot]
            for stop in route:
                if stop == -1:
                    route_points.append(self.depot)
                else:
                    route_points.append(self.points[stop])
            
            # Plot the route
            for j in range(len(route_points) - 1):
                x_values = [route_points[j][0], route_points[j+1][0]]
                y_values = [route_points[j][1], route_points[j+1][1]]
                if route_points[j+1] == self.depot:
                    # Use dashed line for return trips to depot
                    self.ax.plot(x_values, y_values, color=color, linestyle='--', label=f'Route {i+1}' if j == 0 else "")
                else:
                    self.ax.plot(x_values, y_values, color=color, label=f'Route {i+1}' if j == 0 else "")

                # Add arrows
                mid_x = (x_values[0] + x_values[1]) / 2
                mid_y = (y_values[0] + y_values[1]) / 2
                dx = x_values[1] - x_values[0]
                dy = y_values[1] - y_values[0]
                self.ax.arrow(mid_x, mid_y, dx/10, dy/10, shape='full', lw=0, length_includes_head=True, head_width=2, color=color)

        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.legend()
        self.ax.set_title("CVRP Routes")
        self.canvas.draw()

    def update_path_costs(self):
        detailed_costs = self.mra.calculate_detailed_route_costs(self.routes, self.parcels_delivered)
        _, total_distances = self.mra.calculate_route_costs(self.routes)
        self.cost_text.delete('1.0', tk.END)
        
        for i, (route_costs, total_distance) in enumerate(zip(detailed_costs, total_distances)):
            self.cost_text.insert(tk.END, f"Route for DA_{i + 1}:\n")
            for destination, cost, num_parcels in route_costs:
                if destination == "Total":
                    self.cost_text.insert(tk.END, f"  Total Cost: {cost:.2f}\n")
                    self.cost_text.insert(tk.END, f"  Total Distance: {total_distance:.2f}\n")
                    self.cost_text.insert(tk.END, f"  Total Parcels Delivered: {num_parcels}\n")
                    self.cost_text.insert(tk.END, f"  Max Distance: {self.mra.delivery_agents[i].max_distance:.2f}\n")
                    if total_distance > self.mra.delivery_agents[i].max_distance:
                        self.cost_text.insert(tk.END, "  WARNING: Max distance exceeded!\n", "warning")
                else:
                    self.cost_text.insert(tk.END, f"  {destination} (Parcels: {num_parcels}): {cost:.2f}\n")
            self.cost_text.insert(tk.END, "\n")
        
        self.cost_text.tag_configure("warning", foreground="red")

    def on_closing(self):
        if self.route_generation_job:
            self.master.after_cancel(self.route_generation_job)
        self.master.destroy()

def main():
    root = tk.Tk()
    app = CVRPGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()