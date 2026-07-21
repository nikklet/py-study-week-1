students = ["Hermione", "Harry", "Ron"]

for student in students:
     print(student)

for i in range(len(students)): # this counts the number of students in the list and prints their names with a number
     print(i + 1,students[i])

# dict
students = {
    "Hermione": "Gryffindor",
    "Harry": "Gryffindor",
    "Ron": "Gryffindor",
    "Draco": "Slytherin"
}

for student in students:
    print(student, students[student], sep=", ") # this prints the name of the student and their house with a comma in between

students = [
    {"name": "Hermione", "house": "Gryffindor", "patronus": "Otter"},
    {"name": "Harry", "house": "Gryffindor", "patronus": "Stag"},
    {"name": "Ron", "house": "Gryffindor", "patronus": "rat"},
    {"name": "Draco", "house": "Slytherin", "patronus": None}
]

for student in students:
    print(student["name"], student["house"], student["patronus"], sep=", ")