import http.client
import json
import os
import time
from termcolor import colored
import threading


def validate_phone_number(api_key, phone_number, country_hint):
    conn = http.client.HTTPSConnection("api.trestleiq.com")
    headers = {"Content-Type": "application/json"}
    params = f"?api_key={api_key}&phone={phone_number}&country_hint={country_hint}"
    conn.request("GET", "/3.0/phone_intel" + params, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


def sort_and_save_numbers(numbers):
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

        # Introduce a delay between API requests
        time.sleep(1)  # Adjust the delay as needed (e.g., 1 second)

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


# API key, phone numbers file, and country hint
api_key = "O6Kykc2M0kENHwQJbQ2ja0eHA8iLTDE7"
phone_numbers_file = "numx.txt"
country_hint = "US"

# Read phone numbers from file
with open(phone_numbers_file, "r") as file:
    numbers = [line.strip() for line in file]

# Sort and save numbers
sort_and_save_numbers(numbers)
