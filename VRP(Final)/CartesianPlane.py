import random

def generate_random_points(num_points, min_x, max_x, min_y, max_y):
    return [(random.uniform(min_x, max_x), random.uniform(min_y, max_y)) for _ in range(num_points)]

