# Concept:Abstraction
# Q6. Create abstractan class Employee with an abstract method calculate_salary().
# Create subclasses Intern, FullTimeEmployee and ContractEmployee that
# implement the  differently. 
from abc import ABC, abstractmethod


class Employee(ABC):

    @abstractmethod
    def calculate_salary(self):
        pass


class Intern(Employee):

    def calculate_salary(self):
        return 15000


class FullTimeEmployee(Employee):

    def calculate_salary(self):
        return 60000


class ContractEmployee(Employee):

    def calculate_salary(self):
        return 40000


intern = Intern()
full_time = FullTimeEmployee()
contract = ContractEmployee()

print("Intern Salary:", intern.calculate_salary())
print("Full-Time Salary:", full_time.calculate_salary())
print("Contract Salary:", contract.calculate_salary())