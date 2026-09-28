squares = []

for i in range(6):
    squares.append(i*i)

print(squares)

# list-comprehensions

sq = [ i*i for i in range(6) if i%2 != 0]
print(sq)

num = [-1,-3,2,4,-9,9]
num = [0 if i < 0 else i for i in num]
print(num)