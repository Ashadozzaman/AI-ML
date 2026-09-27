# Q2: Given a list of integers compute the average of all numbers in the list.
list = [12,23,43,45]

count = 0
sum = 0
for val in list:
    sum += val
    count += 1

ans = sum/count

print(f"Here is average:{ans}")

#short 
# ans = sum(list)/len(list)