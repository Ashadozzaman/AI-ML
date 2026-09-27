from abc import ABC, abstractmethod

class Payment(ABC):

    @abstractmethod
    def pay(self, amount):
        pass

class BKashPayment(Payment):
    def pay(self,amount):
        print(f"Pain {amount} BDT using Bkash")


class CardPayment(Payment):
    def pay(self,amount):
        print(f"Pain {amount} BDT using Card")

bkash = BKashPayment()
bkash.pay(1000)