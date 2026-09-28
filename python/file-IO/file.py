# f = open("sample2.txt",'x')

# data = f.read() # readline() print 1st line
# print(data)

# w = open("sample.txt","w")
# data1 = f.write('Lorem Ipsum is simply dummy text of \n the printing and typesetting industry.')

# f.close()

with open("sample.txt", "r") as f:
    data = f.read()
    print(data)

#delete file
import os

os.remove("sample2.txt")