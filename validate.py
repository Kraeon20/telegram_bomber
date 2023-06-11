
import os
import requests
import json
from colorama import Fore, Style

API_KEY = "JcFG31W2RMZ0sAwzje27Aqc0l5lamutV"
API_ENDPOINT = "https://api.trestleiq.com/3.1/phone"

# Read phone numbers from the file
def read_phone_numbers(file_path):
    with open(file_path, "r") as file:
        phone_numbers = file.read().splitlines()
    return phone_numbers

# Validate and sort phone numbers
def validate_and_sort_phone_numbers(phone_numbers):
    sorted_numbers = {
        "Unknown": [],
        "Landline": [],
        "Mobile": [],
        "VoIP": [],
        "Toll-Free": []
    }

    for phone_number in phone_numbers:
        # Make API request
        response = requests.get(
            API_ENDPOINT,
            params={
                "api_key": API_KEY,
                "phone": phone_number
            }
        )
        data = response.json()

        # Check if the response is valid
        if response.status_code == 200 and data.get("is_valid"):
            carrier = data.get("carrier")
            line_type = data.get("line_type")

            # Categorize the phone number by carrier and line type
            if carrier in sorted_numbers:
                sorted_numbers[carrier].append(phone_number)
                print(f"{Fore.GREEN}[VALID] {phone_number}{Style.RESET_ALL}")
            else:
                if line_type in sorted_numbers:
                    sorted_numbers[line_type].append(phone_number)
                    print(f"{Fore.GREEN}[VALID] {phone_number}{Style.RESET_ALL}")
                else:
                    sorted_numbers["Unknown"].append(phone_number)
                    print(f"{Fore.GREEN}[VALID] {phone_number}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[INVALID] {phone_number}{Style.RESET_ALL}")

    return sorted_numbers

# Create results folder if it doesn't exist
def create_results_folder():
    if not os.path.exists("results"):
        os.makedirs("results")

# Save sorted numbers to files
def save_sorted_numbers(sorted_numbers):
    for category, numbers in sorted_numbers.items():
        if numbers:
            file_path = f"results/{category}.txt"
            with open(file_path, "w") as file:
                file.write("\n".join(numbers))

# Main program
def main():
    # File path of the phone numbers list
    file_path = "numx.txt"

    # Read phone numbers from file
    phone_numbers = read_phone_numbers(file_path)

    # Validate and sort phone numbers
    sorted_numbers = validate_and_sort_phone_numbers(phone_numbers)

    # Create results folder
    create_results_folder()

    # Save sorted numbers to files
    save_sorted_numbers(sorted_numbers)

    print("Phone numbers validation and sorting completed.")

if __name__ == "__main__":
    main()
