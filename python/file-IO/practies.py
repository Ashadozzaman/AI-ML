data = True
line = 1
with open("sample.txt","r") as f:
    while data:
        data = f.readline()
        if "Python" in data:
            print(f"Word find in line {line} \n {data}")

        line += 1