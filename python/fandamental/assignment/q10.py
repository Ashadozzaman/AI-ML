# Q10. Ask the user for a string and print:
# • All unique characters
# • The count of unique characters

string = input("Enter string: ")

unique_chars = set() # set automatically remove duplicate value

for char in string:
    unique_chars.add(char)

print("Unique characters:", unique_chars)
print("Count of unique characters:", len(unique_chars))