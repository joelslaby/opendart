import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import json

path = "/Users/jslaby/Documents/hobbies/darts/data/cricket/Cricket_2026-03-22_20:40.json"
# img = plt.imshow("/Users/jslaby/Documents/hobbies/darts/opendart/dartboard.png")
with open(path, 'r') as f:
    cricket_data = json.load(f)


def plot_darts(cricket_data):
    for dart in cricket_data['dart_history']:
        match dart['player']:
            case "Jacob":
                color = 'tab:blue'
            case "Joel":
                color = 'tab:green'
            case "Ravi":
                color = 'tab:red'
            case "Dustin":
                color = 'tab:orange'
        x = dart['x']
        y = dart['y']
        plt.scatter(x, y, color=color, s=5)
    
    # plt.imshow(img)
    dartboard = Image.open("/Users/jslaby/Documents/hobbies/darts/opendart/dartboard.png")
    plt.imshow(dartboard)
    plt.show()

plot_darts(cricket_data)