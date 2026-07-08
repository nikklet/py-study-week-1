x = input("what's x? ")
y = input("what's y? ")
# no int hence mathematical numbers are treated as strings and hence 
# merged instead of added.
z = x + y
print(z)

z = int(x) + int(y)
print(z)