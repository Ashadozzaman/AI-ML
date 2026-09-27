# Given List of tupes with info (name,subject)
# list all unique courses
# list student unroll in Chemistry
# create dictinary (student set of courses)
info = [
    ("Rahim", "Math"),
    ("Karim", "English"),
    ("Sakib", "Physics"),
    ("Nadia", "Chemistry"),
    ("Nadik", "Chemistry"),
    ("Rahim", "Chemistry"),
    ("Rahima", "Math"),
    ("Karim", "Physics"),
]
unique_courses = set()
students_ch = []
dict = {}

for name,course in info:
    unique_courses.add(course)
    if course == "Chemistry":
        students_ch.append(name)
    if dict.get(name) == None:
        dict.update({name:set()})
        dict[name].add(course)
    else:
        dict[name].add(course)



print(unique_courses)
print(students_ch)
print(dict)