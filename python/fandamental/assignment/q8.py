# Q8. Write a program to check whether two lists share no common elements.
# share no common elements list1 = [1, 2, 3, 4] list2 = [5, 6, 7, 8]
# share common elements list1 = [1, 2, 3] list2 = [3, 4]
# [Hint - use sets]

list1 = [1, 2, 3, 4, 5]
list2 = [5, 6, 7, 8]

set1 = set(list1)
set2 = set(list2)

union = set1.union(set2) # common and uncommon all
interception = set1.intersection(set2) #common


not_common = []
for i in list1:
    if i in list2:
        # not_common.append(i)
        continue
    else:
        not_common.append(i)

print("Common and unCommon: ",union)
print("common", interception)
print("not_common",not_common)

# list1 = [1, 2, 3] 
# list2 = [3, 4]