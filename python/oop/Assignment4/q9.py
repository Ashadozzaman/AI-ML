# Q9. Create the following classes: Herbivore, Carnivore, Omnivore with some
# attributes & methods. Then create a class `Bear` that inherits from all the above
# classes to showcase how multiple inheritance works.
   
class Herbivore:

    def eat_plants(self):
        print("Eats plants")


class Carnivore:

    def eat_meat(self):
        print("Eats meat")


class Omnivore:

    def eat_both(self):
        print("Eats plants and meat")


class Bear(Herbivore, Carnivore, Omnivore):

    def __init__(self, name):
        self.name = name

    def show_info(self):
        print(f"Bear name: {self.name}")


bear = Bear("Brown Bear")

bear.show_info()
bear.eat_plants()
bear.eat_meat()
bear.eat_both()