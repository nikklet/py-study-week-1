# even and odd numbers
x = int(input("what's x? "))
if x % 2 == 0:
    print("x is even")
else:
    print("x is odd")

# creating a function and using it with Bool
def main():
    x = int(input("what's x? "))
    if is_even(x):
        print("x is even")
    else:
        print("x is odd")

def is_even(n):
    if n % 2 == 0:
        return True
    else:
        return False
# a more concise way to write this statements only allowed in python
def is_even(n):
    return True if n % 2 == 0 else False
# or
def is_even(n):
    return n % 2 == 0

main()