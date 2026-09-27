# n = 312
# while n > 0:
#     print(n%10) # get last digit n%10
#     n = n // 10 # remove last digit

def get_digits(num):
    digits = []
    while num > 0:
        digit = num % 10
        digits.append(digit)
        # print(digit)
        num = num // 10

    for digit in reversed(digits):
        print(digit)
get_digits(312)