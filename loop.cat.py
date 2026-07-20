# while loops
i = 3
while i!= 0: # != means "not equal to"
    print("meow ")
    i = i - 1

# counting up
i = 0
while i < 3:
    print("meow ")
    i += 1

# for loops
for i in range(3): # can change the variable i to _ (underscore) if you don't need to use it
    print("meow ")

# or
print("meow \n" * 3, end="") # prints "meow" 3 times with a new line after each

# while true loop
while True:
    n = int(input("what is n? "))
    if n > 0:
        break

for i in range(n): # underscore can be used instead of i if you don't want to assign it to a variable
    print("meow ")

# creating a function to print meow n times
def main():
    number =  get_number()
    meow(number)


def get_number():
    while True:
        n = int(input("what is n? "))
        if n > 0:
            break
    return n

def meow(n):
    for _ in range(n):
        print("meow ")


main()