try:
    x = int(input("Enter Value: "))
    ans = 100/x
except ZeroDivisionError:
    print(f"Divided bu 0 is not allow")
except ValueError:
    print(f"Invalid value")
else:
    print(f"Answer = {ans}")
finally:
    print(f"Always show this- even arrise exception error")
