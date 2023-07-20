import random
import sqlite3


class Card:

    def __init__(self, pan, pin, balance):
        self.pan = pan
        self.pin = pin
        self.balance = balance

    def add_money(self, cur, conn, income):
        self.balance = self.balance + income
        cur.execute(f"UPDATE card SET balance = {self.balance} WHERE number = {self.pan};")
        conn.commit()

    def remove_money(self, cur, conn, money):
        if self.balance >= money:
            self.balance = self.balance - money
            cur.execute(f"UPDATE card SET balance = {self.balance} WHERE number = {self.pan};")
            conn.commit()
            return True
        else:
            print("Not enough money!")
            return False

    def close_account(self, cur, conn):
        cur.execute(f"DELETE FROM card WHERE number = {self.pan};")
        conn.commit()
        print("The account has been closed!")


class Bank:

    def __init__(self):
        random.seed()
        self.bin = "400000"
        self.conn = sqlite3.connect('card.s3db')
        self.cur = self.conn.cursor()
        if not self.check_exist_table("sequence"):
            self.cur.execute("CREATE TABLE sequence (account_identifier_sequence INTEGER(9));")
            self.cur.execute("INSERT INTO sequence (account_identifier_sequence) VALUES (100000000);")
            self.conn.commit()
        if not self.check_exist_table("card"):
            self.cur.execute("CREATE TABLE card (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, pin TEXT, balance INTEGER DEFAULT 0);")
            self.conn.commit()

    @staticmethod
    def print_welcome_menu():
        print("1. Create an account")
        print("2. Log into account")
        print("0. Exit")

    @staticmethod
    def print_account_menu():
        print("1. Balance")
        print("2. Add income")
        print("3. Do transfer")
        print("4. Close account")
        print("5. Log out")
        print("0. Exit")

    @staticmethod
    def print_message_wrong_menu_item():
        print("Wrong item number!")

    @staticmethod
    def print_goodbye_message():
        print("Bye!")

    @staticmethod
    def calculate_checksum_by_luhn_algorithm(account_identifier):
        sum_digit = 0
        list_account_identifier = list(account_identifier)
        for k in range(0, len(list_account_identifier)):
            digit = int(list_account_identifier[k])
            if k % 2 == 0:
                sum_digit += digit * 2 if digit * 2 < 9 else digit * 2 - 9
            else:
                sum_digit += digit
        checksum = 0 if sum_digit % 10 == 0 else 10 - sum_digit % 10
        return str(checksum)

    def validate_card_number(self, crd_number):
        if crd_number[15] != self.calculate_checksum_by_luhn_algorithm(crd_number[0:15]):
            print("Probably you made a mistake in the card number. Please try again!")
            return False
        else:
            return True

    def authorise_card(self, pan, pin):
        crd = self.cur.execute(f"SELECT * FROM card WHERE number = {pan} and pin = {pin};").fetchone()
        if crd:
            crd = Card(crd[1], crd[2], crd[3])
            return crd
        else:
            print("Wrong card number or PIN!")
            return False

    def search_card(self, pan):
        crd = self.cur.execute(f"SELECT * FROM card WHERE number = {pan};").fetchone()
        if crd:
            crd = Card(crd[1], crd[2], crd[3])
            return crd
        else:
            print("Such a card does not exist.")
            return False

    def check_exist_table(self, table_name):
        try:
            self.cur.execute(f"SELECT * FROM {table_name};")
        except sqlite3.OperationalError:
            return False
        return True

    def take_next_account_identifier(self):
        next_account_identifier = self.cur.execute("SELECT * FROM sequence;").fetchone()[0]
        k = int(next_account_identifier) + 1
        self.cur.execute(f"UPDATE sequence SET account_identifier_sequence = {k};")
        self.conn.commit()
        return str(next_account_identifier)

    def create_card(self):
        account_identifier_sequence = self.take_next_account_identifier()
        pan = self.bin + account_identifier_sequence + self.calculate_checksum_by_luhn_algorithm(
            self.bin + account_identifier_sequence)
        pin = str(random.randint(1000, 9999))
        self.cur.execute(f"INSERT INTO card(number, pin) VALUES ({pan}, {pin});")
        self.conn.commit()
        created_card = Card(pan, pin, 0)
        return created_card

    def log_into_account(self, open_card):
        while True:
            self.print_account_menu()
            k = input()
            if k == "1":
                print(f"Balance:{open_card.balance}")
            elif k == "2":
                print("Enter income:")
                income = int(input())
                open_card.add_money(self.cur, self.conn, income)
                print("Income was added!")
            elif k == "3":
                print("Transfer")
                print("Enter card number:")
                input_receive_card_number = input()
                receive_card = None
                if self.validate_card_number(input_receive_card_number):
                    receive_card = self.search_card(input_receive_card_number)
                if receive_card and receive_card.pan == open_card.pan:
                    print("You can't transfer money to the same account!")
                elif receive_card:
                    print("Enter how much money you want to transfer:")
                    transfer_sum = int(input())
                    if open_card.remove_money(self.cur, self.conn, transfer_sum):
                        receive_card.add_money(self.cur, self.conn, transfer_sum)
                        print("Success!")
            elif k == "4":
                open_card.close_account(self.cur, self.conn)
                return True
            elif k == "5":
                print("You have successfully logged out!")
                return True
            elif k == "0":
                return False
            else:
                self.print_message_wrong_menu_item()


bank = Bank()
while True:
    bank.print_welcome_menu()
    i = input()
    if i == "1":
        new_card = bank.create_card()
        print("Your card has been created")
        print("Your card number:")
        print(new_card.pan)
        print("Your card PIN:")
        print(new_card.pin)
    elif i == "2":
        print("Enter your card number:")
        input_pan = input()
        print("Enter your PIN:")
        input_pin = input()
        card = bank.authorise_card(input_pan, input_pin)
        if card:
            print("You have successfully logged in!")
            log_out = bank.log_into_account(card)
            if log_out is False:
                bank.print_goodbye_message()
                break
    elif i == "0":
        bank.print_goodbye_message()
        break
    else:
        bank.print_message_wrong_menu_item()
