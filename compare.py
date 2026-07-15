# conditionals
x = int(input("what's x? "))
y = int(input("what's y? "))

if x < y:
    print("x is less than y")
elif x > y:
    print("x is greater than y")
else:
    print("x is equal to y")
# else statements
if x < y or x > y:
    print("x is not equal to y")
else:
    print("x is equal to y")

# Not
if x != y:
    print("x is not equal to y")
else:
    print("x is equal to y")

# equal
if x == y:
    print("x is equal to y")
else:
    print("x is not equal to y")