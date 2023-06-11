import http.client
import json
import os
from termcolor import colored
import threading
import random

def validate_phone_number(api_key, phone_number, country_hint):
    conn = http.client.HTTPSConnection("api.trestleiq.com")
    headers = {"Content-Type": "application/json"}
    params = f"?api_key={api_key}&phone={phone_number}&country_hint={country_hint}"
    conn.request("GET", "/3.0/phone_intel" + params, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


def sort_and_save_numbers(numbers, api_key, country_hint):
    results = {}
    lock = threading.Lock()  # Lock to ensure thread-safe writing to files and printing

    def process_number(number):
        response = validate_phone_number(api_key, number, country_hint)
        carrier = response.get("carrier")
        is_valid = response.get("is_valid")

        if is_valid and carrier:
            with lock:
                if carrier not in results:
                    results[carrier] = []
                results[carrier].append(number)

                # Save the validated number to the carrier's file
                filename = f"results/{carrier}.txt"
                if not os.path.exists("results"):
                    os.makedirs("results")
                with open(filename, "a") as file:
                    file.write(number + "\n")

                # Print valid number in green
                print(colored(f"Valid number: {number}", "green"))
        else:
            # Print invalid number in red
            with lock:
                print(colored(f"Invalid number: {number}", "red"))

    # Create and start threads for processing each number
    threads = []
    for number in numbers:
        thread = threading.Thread(target=process_number, args=(number,))
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("Numbers sorted and saved successfully!")


def generate_numbers():
    numbers = [str(random.randint(1000000000, 9999999999)) for _ in range(10)]
    sort_and_save_numbers(numbers, api_key, country_hint)


def validate_and_sort_numbers():
    filename = input("Enter the name of the file to import for validation: ")
    if not os.path.exists(filename):
        print("File not found.")
        return
    
    with open(filename, "r") as file:
        numbers = [line.strip() for line in file]
    
    sort_and_save_numbers(numbers, api_key, country_hint)


# API key, phone numbers file, and country hint
api_key = "CfuNndQGGjDvOO9Onx2zAXcAzLHTKsrQdgxW6Uod58lgJCJf"
country_hint = "US"

while True:
    print("Main Page:")
    print("1. Generate Numbers")
    print("2. Validate and Sort Numbers")
    print("3. Exit")
    choice = input("Enter your choice (1-3): ")
    
    if choice == "1":
        generate_numbers()
    elif choice == "2":
        validate_and_sort_numbers()
    elif choice == "3":
        break
    else:
        print("Invalid choice. Please try again.")
