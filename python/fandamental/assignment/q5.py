students = {}

while True:
    print("\nA - Add a student")
    print("B - Update marks")
    print("C - Search for a student")
    print("D - Display all students and marks")
    print("Q - Quit")

    choice = input("Please enter your choice:").upper()

    # A - add student

    if choice == "A":
        name = input("Enter Name")
        mark = int(input("Enter Mark"))

        students[name] = mark

        print("Student Add Successfully")
    elif choice == "B":
        if name in students:
            mark = int(input("Enter New Marks:"))
            students[name] = mark
            print("Student Mark Update Successfully")
        else:
            print("Student Not Found") 
    # C - Search student
    elif choice == "C":
        name = input("Enter student name: ")

        if name in students:
            print(f"{name}'s marks: {students[name]}")
        else:
            print("Student not found.")

    # D - Display all
    elif choice == "D":
        if len(students) == 0:
            print("No students found.")
        else:
            for name, marks in students.items():
                print(f"{name}: {marks}")

    # Quit
    elif choice == "Q":
        print("Program ended.")
        break

    else:
        print("Invalid choice.")

