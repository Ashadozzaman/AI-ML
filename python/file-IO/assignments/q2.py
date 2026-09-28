# Q2: Create a program that
# 1. Opens a file in append mode"log.txt"
# 2. Adds a new log entry (like "Program run successfully")
# 3. Opens the file in read mode and prints all logs

with open('files/log.txt', 'a') as f:
    f.write("Program run successfully\n")

with open('files/log.txt', 'r') as f:
    data = f.read()
    print(data)