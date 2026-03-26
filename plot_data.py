import pandas as pd
import matplotlib.pyplot as plt

def load_data(data_path, data_file):
    return pd.read_pickle(data_path+data_file+".pkl")



data_path = "/Users/jslaby/Documents/projects/darts/data/cricket/"
data_file = "Cricket_2026-03-22_22:01"

df = load_data(data_path, data_file)

for i, team in enumerate([1236, 930]):
    plt.plot(df[df.team==i]["team_score_after"], label=f"Team {team}")
plt.legend()
plt.grid()
plt.show()
# print(df[df.team==0]["team_score_after"])