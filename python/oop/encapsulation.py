class BankAccount:
    def __init__(self, name, balance):
        self.name= name
        self.__balance = balance #__ is decler private

    def get_balance(self): #getter
        return self.__balance


    def set_balance(self, newBalance): #setter
        self.__balance = newBalance

ac1 = BankAccount('Asad',1000)
ac1.set_balance(2000)
print(ac1.get_balance());