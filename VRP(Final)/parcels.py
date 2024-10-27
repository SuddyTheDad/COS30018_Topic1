import sys
import os
import random
import csv

class Package:
    def __init__(self, customer_id, destination, num_parcels):
        self.customer_id = customer_id 
        self.destination = destination  
        self.num_parcels = num_parcels  

    @staticmethod
    def create_parcels(num_parcels, points):
        packages = []
        customer_ids = [f"C{i + 1}" for i in range(num_parcels)]
        
        for i in range(num_parcels):
            destination = points[i % len(points)]  # If all points have parcels cycle through again
            num_parcels = random.randint(1, 5)
            package = Package(customer_ids[i], destination, num_parcels)
            packages.append(package)
        
        return packages


    @staticmethod
    def save_packages(packages, filename="parcel_info.txt"):
        parcel_data = [
            {
                'customer_id': p.customer_id,
                'destination': p.destination,
                'num_parcels': p.num_parcels
            }
            for p in packages
        ]
        write_parcels_to_file(parcel_data, filename)

def read_file(filename):
    parcels = []
    with open(filename, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            customer_id, x, y, num_parcels = row
            parcels.append({
                'customer_id': customer_id,
                'destination': (float(x), float(y)),
                'num_parcels': int(num_parcels)
            })
    return parcels

def write_parcels_to_file(parcels, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Customer ID', 'X', 'Y', 'Number of Parcels'])
        for parcel in parcels:
            writer.writerow([
                parcel['customer_id'],
                f"{parcel['destination'][0]:.2f}",
                f"{parcel['destination'][1]:.2f}",
                parcel['num_parcels']
            ])
