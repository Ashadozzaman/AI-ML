# Concept: Constructor Overloading (with Default Parameters)
# Q7. Create a class Person that allows the constructor to work with 
# • name only
# • name + age
# • name + age + address
# As direct constructor overloading (multiple constructors) are not allowed but
# we have to use to simulate constructor overloading. 

class Person:

    def __init__(self, name, age=None, address=None):
        self.name = name
        self.age = age
        self.address = address

    def get_info(self):
        print(f"Name: {self.name}")

        if self.age is not None:
            print(f"Age: {self.age}")

        if self.address is not None:
            print(f"Address: {self.address}")


# Name only
person1 = Person("Ashad")

# Name + age
person2 = Person("Ashad", 30)

# Name + age + address
person3 = Person("Ashad", 30, "Dhaka")


person1.get_info()

print("---")

person2.get_info()

print("---")

person3.get_info()