# Concept: Instance & Class Attributes
# Q8. Create a class with:Player
# • a class variable player_count
# • instance variables name and level
# Track how many players were created

class Player:

    # Class attribute
    player_count = 0

    def __init__(self, name, level):

        # Instance attributes
        self.name = name
        self.level = level

        # Increase player count
        Player.player_count += 1


player1 = Player("Ashad", 10)
player2 = Player("Rahim", 15)
player3 = Player("Karim", 20)

print("Player 1:", player1.name, player1.level)
print("Player 2:", player2.name, player2.level)
print("Player 3:", player3.name, player3.level)

print("Total Players:", Player.player_count)