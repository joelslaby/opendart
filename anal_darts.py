import json
from dart_engine.params_cricket import Team
from dart_engine.helpers_cricket import get_game_marks_sum
from matplotlib import pyplot as plt

CRICKET_NUMBERS = [20,19,18,17,16,15,25]

def main():
    
    for game in range(3):
        filename = f"../Games_20260322/Cricket/Game_{game+1}.json"
        # Open the file in read mode ('r')
        with open(filename, 'r') as file:
            # Deserialize the JSON data from the file into a Python object (e.g., a dictionary)
            data = json.load(file)

        teams = [
                Team("1236", "Jacob", "Joel"),
                Team("930", "Dustin", "Ravi")
            ]
        dart_history = data["dart_history"]

        p0_marks = get_game_marks_sum(dart_history,teams,teams[0].players[0])
        p1_marks = get_game_marks_sum(dart_history,teams,teams[0].players[1])
        p2_marks = get_game_marks_sum(dart_history,teams,teams[1].players[0])
        p3_marks = get_game_marks_sum(dart_history,teams,teams[1].players[1])


        plt.figure()
        plt.xlabel("Turn")
        plt.ylabel("Marks")
        plt.plot(range(len(p0_marks)),p0_marks,label=teams[0].players[0].name)
        plt.plot(range(len(p1_marks)),p1_marks,label=teams[0].players[1].name)
        plt.plot(range(len(p2_marks)),p2_marks,label=teams[1].players[0].name)
        plt.plot(range(len(p3_marks)),p3_marks,label=teams[1].players[1].name)
        plt.legend()
        plt.savefig(f"plot{game+1}.png")

main()