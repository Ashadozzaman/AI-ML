def salary_vat_calculation(salary):
    vat = 0
    if(salary < 30000):
        vat = (salary * 5)/100
    elif(salary < 30000 or salary > 70000):
        vat = (salary * 15)/100
    else:
        vat = (salary * 25)/100

    return vat

salary = int(input("Enter Salary:"))
print(salary_vat_calculation(salary))

