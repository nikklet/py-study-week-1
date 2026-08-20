# for the height and length of column, row
#def main():
#    print_column(3)

#def print_column(height):
#    for i in range(height):
#        print("#")

#main()

#def main():
#    print_row(4)

#def print_row(width):
#    print("?" * width)

#main()

def main():
    print_square(3)

def print_square(size):

    # for each row in the square
    for i in range(size):
        
        # for each brick in one row
        for j in range(size):

            # print("#", end="") # this prints a "#" without a new line
            print("#", end="")
        print() # this prints a new line after each row

# or a shorter way
#def print_square(size):
#    for i in range(size):
#        print("#" * size) which prints a row of "#" for the size of the square

main()