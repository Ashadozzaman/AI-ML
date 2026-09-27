# Given a tuple of integers, create:
# • A tuple of all even numbers
# • A tuple of all odd numbers
numbers = (1,2,3,4,5,6)

even = ()
odd = ()
for i in numbers:
    if i % 2 == 0:
        even = even + (i,)
    else:
        odd = odd + (i,)


print(even)
print(odd)
