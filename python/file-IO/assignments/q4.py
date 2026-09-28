# Q4. Create a Python dictionary of 3 cities and their populations. Save it to "cities.json"
# 1. Then load the JSON and print each city and its population.
# 2. Ask the user for a new city & its population - update this info in the json file

import json

cities = {
    "Dhaka": 10000000,
    "Chittagong": 5000000,
    "Rajshahi": 1000000
}

# 1. Save dictionary to cities.json
with open("files/cities.json", "w") as f:
    json.dump(cities, f, indent=4)


# 2. Load JSON and print each city and population
with open("files/cities.json", "r") as f:
    cities = json.load(f)

for city, population in cities.items():
    print(f"{city}: {population}")


# 3. Ask user for a new city and population
new_city = input("Enter a new city: ")
new_population = int(input("Enter population: "))

# Update dictionary
cities[new_city] = new_population


# 4. Save updated dictionary back to JSON
with open("files/cities.json", "w") as f:
    json.dump(cities, f, indent=4)

print("City added successfully!")