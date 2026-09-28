# Q1: Create a program that
# 1. Opens a file in write mode"names.txt"
# 2. Writes 5 names (one per line) entered by the user
# 3. Then opens the same file in read mode and prints all names
with open("files/names.txt","w") as f:
    for i in range(5):
        names = input(f"Enter Names {i + 1}:")
        f.write(names + "\n")

with open("files/names.txt", "r") as f:
    data = f.read()
    print("\nNames:")
    print(data)