class Student:
    college = "College ABC" # class attributes
    def __init__(self,name,email): #perameterized
        self.name = name # instence  attributes
        self.email = email

    def get_email(self):
        return self.email

    @classmethod # decler class methode
    def get_college_name(cls):
        print(f"College name is: {cls.college}")

    @staticmethod # static method
    def sum(a, b):
        return f"Sum: {a + b}"

student1 = Student("Asad","asad@gmail.com")
student2 = Student("Karim","karim@gmail.com")

print(Student.get_college_name())
print(student1.get_email())
print(student2.sum(10,1000))