class Employee:
    start_time = "10 am"
    end_time = "6 pm"

class AdminStaff(Employee):
    def __init__(self, role):
        self.role = role

class AccStaff(AdminStaff):
    def __init__(self, salary,role):
        super().__init__(role)
        self.salary = salary

class SupperAdmin(AccStaff, AdminStaff): # Multiple Inharitance
    def __init__(self, role,salary):
        AdminStaff.__init__(self,role)
        AccStaff.__init__(self,salary,role)

        self.salary = salary
        self.role = role

staff = AdminStaff("Manager")
acc1 = AccStaff('250000',"CA")

sp1 = SupperAdmin("Admin",100000)
print(sp1.role, sp1.salary)
# print(acc1.role, acc1.salary, acc1.start_time, acc1.end_time)