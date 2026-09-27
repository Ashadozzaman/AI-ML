# Q3. Create a class Student with attributes _name, _roll_no, and _marks.
# Provide getter and setter methods with validation (e.g., marks cannot be
# negative, roll number has to be between 1 & 100 & name cannot be empty).

class Student:
    def __init__(self,name,roll_no,mark):
        self.__name = name
        self.__roll_no = roll_no
        self.__mark = mark

    # Getter
    def get_std_info(self):
        print(
            f"Student Details:\n"
            f"Name: {self.__name}\n"
            f"Roll: {self.__roll_no}\n"
            f"Marks: {self.__mark}"
        )

    #setter
    def set_std_info(self,name,roll_no,mark):
        if name == '':
            print('Student Name Not Null')
            return
        elif(roll_no < 1 or roll_no > 100):
            print("roll number has to be between 1 & 100")
            return
        elif(mark < 0):
            print("Mark Must Be Positive value")
            return
        else:
            print("Student Add Successfully")

        self.__mark = mark
        self.__roll_no = roll_no
        self.__name = name

        print("Student updated successfully")

std = Student('Ashadozzaman', 12, 89)
#get Student
std.get_std_info()

#Set Student
std.set_std_info("Asad",-1,80)

# Get updated student
std.get_std_info()