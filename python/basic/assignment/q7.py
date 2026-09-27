# Design a program to continuously input a number from user & print if it is
# positive or negative until the user enters “Quit”.

while True:
    value = input("Enter Value:")

    if value == "Quit":
        break

    number = int(value)

    if number > 0:
        print("Positive")
    elif(number < 0):
        print("Nagative")
    else:
        print("Zero")