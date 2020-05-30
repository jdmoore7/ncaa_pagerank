# SQL
import sqlite3
conn = sqlite3.connect('acc1819.db')
c = conn.cursor()

# Get columns from game table
game_columns = c.execute("""
PRAGMA table_info(games);
""").fetchall()
g_col = [game_columns[i][1] for i in range(len(game_columns))]

# Get columns from box table
box_columns = c.execute("""
PRAGMA table_info(box_scores);
""").fetchall()
b_col = [box_columns[i][1] for i in range(len(box_columns))]

# Join tables on GameId
join_tuples = c.execute("""
SELECT *
FROM games g
INNER JOIN
  box_scores b
    ON g.GameId = b.GameId
""").fetchall()

join_col = []
join_col.extend(g_col+b_col)

# Create Dataframe with appropriate column names
import pandas as pd
game_frame = pd.DataFrame(join_tuples,columns=join_col) # removes GameId col (once) which occurrs twice.
df = game_frame.loc[:,~game_frame.columns.duplicated()]

# For each GameID, find difference between scores and send to list
scores = df.groupby('GameId')['Score'].diff().to_list()
import numpy as np
scores = [scores[idx+1]*(-1) if np.isnan(s) == True else s for idx,s in enumerate(scores)]
df['delta'] = scores
regular_season = df[df['NeutralSite']==0]

# Make sure we build edges between teams where the delta is pointing the RIGHT direction
edges = []
for idx,row in regular_season.iterrows():
  if idx % 2 == 1:
    continue
  else:
    g_id = row[1]
    away = row[3]
    home = row[4]
    relative_team = row[5]
    delta = row[22]
    
    if relative_team == away:
      delta = -1* delta

    if delta > 0:
      winner = home
      loser = away
      points = delta
    elif delta <0:
      winner = away
      loser = home
      points = delta * -1
    else:
      continue

    edges.append((loser,winner,points)) #creating a network of who has beaten who. 
    
import igraph
game_graph = igraph.Graph.TupleList(edges,weights=True,directed=True)
## This design allows points to travel FROM the losing team TO the winning team.

import operator
vectors = game_graph.pagerank()
e = {name:cen for cen, name in  zip([v for v in vectors],game_graph.vs['name'])}
sorted_eigen = sorted(e.items(), key=operator.itemgetter(1),reverse=True)

print("""
My results, note no random seed was set.

[('Virginia Cavaliers', 0.13017375369587267),
 ('Duke Blue Devils', 0.1281557242167233),
 ('North Carolina Tar Heels', 0.11046094392415888),
 ('Louisville Cardinals', 0.10038343125194146),
 ('Syracuse Orange', 0.0738918604999491),
 ('Virginia Tech Hokies', 0.07338334328560789),
 ('Florida State Seminoles', 0.06631513350172268),
 ('Clemson Tigers', 0.05021274431235776),
 ('Boston College Eagles', 0.04853355910234985),
 ('North Carolina State Wolfpack', 0.043844039711496204),
 ('Pittsburgh Panthers', 0.04351408651651734),
 ('Georgia Tech Yellow Jackets', 0.041049895707065284),
 ('Miami (FL) Hurricanes', 0.03353472714756832),
 ('Wake Forest Demon Deacons', 0.030374053695965898),
 ('Notre Dame Fighting Irish', 0.0261727034307033)]
""")

rankings = [(i,tup[0],tup[1]) for i,tup in enumerate(sorted_eigen)]
import csv
with open('ExampleRankings.csv', 'w', newline='') as csvfile:
    fieldnames = ['ranking','team','eigenvector centrality']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for edge in rankings:
        writer.writerow({
                        'ranking': edge[0]+1,
                        'team': edge[1],
                        'eigenvector centrality': edge[2]
        })
