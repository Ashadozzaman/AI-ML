#Function overriding

class Employee:
    def get_designation(self):
        print(f"designation = Employee")

class Teacher(Employee):
    def get_designation(self):
        print(f"designation = Teacher")


obj = Teacher()
obj.get_designation()

# Duck Typing
