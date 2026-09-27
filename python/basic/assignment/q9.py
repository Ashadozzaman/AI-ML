# Write a function is_prime(n) that returns True if n is a prime number and false otherwise, using a loop
def is_prime(n):

    is_prime = True

    if n < 2:
        is_prime = False
    else:
        for i in range(2, n-1):
            if n % i == 0:
                is_prime = False
                break
    if is_prime:
        return "Prime"
    else:
        return "Not Prime"
    
number = int(input("Enter Number:"))
print(is_prime(number))
