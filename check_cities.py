import sqlite3
import random

db_path = "state.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get processed searches
cursor.execute("SELECT search_key FROM processed_searches")
rows = cursor.fetchall()

city_counts = {}
for row in rows:
    key = row[0]
    if '|' in key:
        city = key.split('|')[1]
        city_counts[city] = city_counts.get(city, 0) + 1

# Read current cities
with open("cities.txt", "r") as f:
    current_cities = [c.strip() for c in f if c.strip()]

# Keywords count
keywords_count = 20

completed_cities = []
for city in current_cities:
    if city_counts.get(city, 0) >= keywords_count:
        completed_cities.append(city)

print(f"Total current cities: {len(current_cities)}")
print(f"Completed cities: {len(completed_cities)}")
for c in completed_cities:
    print(f" - {c} (Completed: {city_counts.get(c, 0)}/{keywords_count})")
    
# Let's see what cities have SOME progress but not all
in_progress = []
for city in current_cities:
    if 0 < city_counts.get(city, 0) < keywords_count:
        in_progress.append(city)
        
print(f"In progress cities: {len(in_progress)}")
for c in in_progress:
    print(f" - {c} (Progress: {city_counts.get(c, 0)}/{keywords_count})")
