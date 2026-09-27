# Ask the user for a string and check whether it is a palindrome or not.
string = input("Enter String:")
if(string == string[::-1]):
    print("Palindrome")
else:
    print("Not Palindrome")
