# Ask for the users name
name = input("what is your name?")
print("hello, " + name)
# or
print("hello, ", end="")
print(name)
# remove whitespace from str and capitalize the name
name = name.strip().title()

#  capitalize the first letter of the name
print(f"hello, {name}")

# combination for a cleaner code and save some lines of code and time
name = input("what is your name?").strip().title()
# split the name into first and last name
first, last = name.split(" ")
print(f"hello, {first}")