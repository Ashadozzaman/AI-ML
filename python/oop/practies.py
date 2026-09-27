class Product():
    products = []
    def __init__(self,name,price,discount):
        self.name = name
        self.price = price
        self.discount = discount
        discountPrice = self.cal_discount(price,discount)

        Product.products.append({
            "name":name,
            "price":price,
            "discount":discount,
            "discountPrice":discountPrice
        })

    @classmethod
    def get_all_products(cls):
        print("\n---All Products---")

        for product in cls.products:
            print(
                f"Name: {product['name']}, "
                f"Price: {product['price']}, "
                f"Discount: {product['discount']}%,"
                f"discountedPrice: {product['discountPrice']}%,"
            )


    @staticmethod
    def cal_discount(price,discount):
        return price - (price * discount)/100


def input_product():
    name = input("Enter Product Name: ")
    price = int(input("Enter Product price: "))
    discount = int(input("Enter Product discount: "))

    product = Product(name,price,discount)
 
while True:
    input_product()

    choice = input("Do you want to add another product? (y/n): ")

    if choice.lower() != "y":
        break

Product.get_all_products()  