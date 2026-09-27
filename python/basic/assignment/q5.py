# Write a function to return the sum of digits of a number, n.
def sum_number(number):
    total = 0

    while number > 0:
        digit = number % 10
        total = total + digit
        number = number // 10

    return total


number = int(input("Enter number: "))
print(sum_number(number))