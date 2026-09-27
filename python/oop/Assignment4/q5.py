# Concept:Inheritance
# Q5. Create a base class  Vehicle with attributes like brand and model.
# Create two subclass Car and Bike that add extra attributes - seats (in Car) & engine_cc (in Bike).

class Vehicle:
    brand = "Test"
    model = "M0Test"
    def __init__(self,brand,model):
        self.brand = brand
        self.model = model

class Car(Vehicle):
    def __init__(self,brand,model,seats):
        super().__init__(brand,model)
        self.seats = seats

    def get_car_info(self): 
        print(
            f"Car Info\n"
            f"Brand: {self.brand}\n"
            f"Model: {self.model}\n"
            f"Seats: {self.seats}"
        )

class Bike(Vehicle):
    def __init__(self,brand,model, engine_cc):
        super().__init__(brand,model)
        self.engine_cc = engine_cc

    def get_bike_info(self): 
        print(
            f"Bike Info\n"
            f"Brand: {self.brand}\n"
            f"Model: {self.model}\n"
            f"Engine CC: {self.engine_cc}"
        )


car = Car("Toyota", "Corolla", 5)
car.get_car_info()

bike = Bike("Yamaha", "R15", 155)
bike.get_bike_info()