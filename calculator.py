x = input("what's x? ")
y = input("what's y? ")
# no int hence mathematical numbers are treated as strings and hence 
# merged instead of added.
z = x + y
print(z)

z = int(x) + int(y)
print(z)

# a shorter version of the above code
x = int(input("what's x? "))
y = int(input("what's y? "))

print(x + y)

# using decimal point with float
x = float(input("what's x? "))
y = float(input("what's y? "))

print(x + y)

# rounding up integers 
x = float(input("what's x? "))
y = float(input("what's y? "))

z = round(x + y)

print(z)

# adding comma with the f= format 
x = float(input("what's x? "))
y = float(input("what's y? "))

z = round(x + y)
# use print(z) if u dont want comma
print(f"{z:,}")

#
x = float(input("what's x? "))
y = float(input("what's y? "))

z = x / y
print(z)

# to decide the nuber of digits you want to round up to
z = round(x /y, 2)
print(z)
# or
z = x / y
print(f"{z:.3f}")