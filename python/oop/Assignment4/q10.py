# Concept:OOP
# Q10. Mini Project – OOP Chat System
# Letʼs create a Chat System using OOPs concepts. We have to create classes:
# • User
# • Message
# • ChatRoom
# And we have to implement functions:
# • sending messages
# • viewing chat history
# • user joining and leaving the chatroom

class User:

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class Message:

    def __init__(self, sender, text):
        self.sender = sender
        self.text = text

    def display(self):
        print(f"{self.sender}: {self.text}")


class ChatRoom:

    def __init__(self, name):
        self.name = name
        self.users = []
        self.messages = []

    def join(self, user):
        if user not in self.users:
            self.users.append(user)
            print(f"{user} joined {self.name}")
        else:
            print(f"{user} is already in the room")

    def leave(self, user):
        if user in self.users:
            self.users.remove(user)
            print(f"{user} left {self.name}")
        else:
            print(f"{user} is not in the room")

    def send_message(self, user, text):

        if user not in self.users:
            print(f"{user} cannot send message. Please join the room first.")
            return

        message = Message(user, text)
        self.messages.append(message)

        print(f"{user} sent a message")

    def chat_history(self):

        print(f"\n--- {self.name} Chat History ---")

        if not self.messages:
            print("No messages yet")
            return

        for message in self.messages:
            message.display()


# Create users
user1 = User("Ashad")
user2 = User("Rahim")
user3 = User("Karim")


# Create chat room
room = ChatRoom("Python Developers")


# Users join
room.join(user1)
room.join(user2)
room.join(user3)


# Send messages
room.send_message(user1, "Hello everyone!")
room.send_message(user2, "Hi Ashad!")
room.send_message(user3, "How are you?")


# View chat history
room.chat_history()


# User leaves
room.leave(user3)


# Try sending after leaving
room.send_message(user3, "I am back!")


# View history again
room.chat_history()