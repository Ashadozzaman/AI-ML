# Q7: Write a program that takes a string from the user and prints the number of spaces in the string.

string = input("Enter String here: ")

count = 0

for char in string:
    if char == " ":
        count += 1

print(f"Number of spaces: {count}")


