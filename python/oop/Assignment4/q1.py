# Q1:  Create a BankAccount class with attributes account_number ,owner_name and balance.
# Add methods to deposit, withdraw check balance

class BankAccount:
    def __init__(self,account_number,owner_name,balance):
        self.account_number = account_number
        self.owner_name = owner_name
        self.__balance = balance

    def deposit(self,amount):
        self.__balance += amount
        print(f"Deposited: {amount}")

    def withdraw(self,amount):
        if amount <= self.__balance:
            self.__balance -= amount
            print(f"Withdrow: {amount}")
        else:
            print("Insufficient balance")

    def check_balance(self):
        print(f"Balance: {self.__balance}")

account = BankAccount("123456", "Ashad", 5000)

account.check_balance()

account.deposit(2000)

account.check_balance()

account.withdraw(1000)

account.check_balance()