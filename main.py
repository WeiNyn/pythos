import math

def print_rectangle(area):
    # Simple rectangle with width:height ratio of 2:1
    height = int(math.sqrt(area / 2)) 
    width = 2 * height
    if height == 0 or width == 0:
        print("Cannot print rectangle with area 0")
        return
    for _ in range(height):
        print('* ' * width)

def print_square(area):
    side = int(math.sqrt(area))
    if side == 0:
        print("Cannot print square with area 0")
        return
    for _ in range(side):
        print('* ' * side)

def print_triangle(area):
    # Right-angled triangle, area = 0.5 * base * height, assume base = height for simplicity initially
    side = int(math.sqrt(2 * area)) # area = 0.5 * side * side => side = sqrt(2 * area)
    if side == 0:
        print("Cannot print triangle with area 0")
        return
    for i in range(1, side + 1):
        print('* ' * i)


if __name__ == "__main__":
    try:
        num_str = input("Enter a number: ")
        num = float(num_str)
        square_area = num * num
        print(f"The square of {num} is {square_area}")

        shape_choice = input("Choose a shape (rectangle, square, triangle): ").lower()

        if shape_choice == 'rectangle':
            print("Printing a rectangle with area approximately equal to the square of the number:")
            print_rectangle(square_area)
        elif shape_choice == 'square':
            print("Printing a square with area approximately equal to the square of the number:")
            print_square(square_area)
        elif shape_choice == 'triangle':
            print("Printing a triangle with area approximately equal to the square of the number:")
            print_triangle(square_area)
        else:
            print("Invalid shape choice.")

    except ValueError:
        print("Invalid input. Please enter a valid number.")