# Q2 Create a class Book with the following attributes:
# • title
# • author
# • list of reviews
# And add methods to:
# • add a new review
# • count reviews
# • display all reviews
# Concept Class & Object
class Book:

    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.reviews = []

    def add_new_review(self,review):
        self.reviews.append({ 
            review:review
        })
 
    def count_reviews(self):
        return len(self.reviews);

    def display_all_reviews(self):
        for review in self.reviews:
            print(review)

# Create book
book = Book("Atomic Habits", "James Clear")

# Add Reviews
book.add_new_review('very usefull book')
book.add_new_review("Easy to understand")
book.add_new_review("Highly recommended")

print("Total Reviews: ",book.count_reviews())

# Display reviews
book.display_all_reviews()