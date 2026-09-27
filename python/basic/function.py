# defination
def average(a,b,c):
    avg = (a+b+c)/3
    return avg

print(average(3,3,3))

#  factorial calculation
# n = int(input("Enter Number: "))

def calculate_factorial(n):
    fact = 1
    for val in range(1,n+1):
        fact = fact * val
    return fact

print(calculate_factorial(5))