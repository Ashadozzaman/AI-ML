def even_number(a,b):
    for i in range(a,b):
        i += 1
        if(i % 2 == 0):
            print("Even Number:",i)

even_number(1,10)