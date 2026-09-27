# Q4: Create a class Shape with a method area().
# Create subclasses Circle, Rectangle, and Triangle that override the area() method.
# Concept: Function Overriding

class Shape:
    def area(self):
        pass

class Circle(Shape):
    def __init__(self,radius):
        self.radius = radius

    def area(self):
        return 3.1416 * self.radius ** 2

class Rectangle(Shape):
    def __init__(self, height, width):
        self.height = height 
        self.width = width 

    def area(self):
        return self.height *  self.width

class Triangle(Shape):
    def __init__(self,base,height):
        self.height = height 
        self.base = base 
         
    def area(self):
        return .5 * self.base * self.height

circle = Circle(5)
rectangle = Rectangle(10, 5)
triangle = Triangle(10, 6)

print("Circle:", circle.area())
print("Rectangle:", rectangle.area())
print("Triangle:", triangle.area())