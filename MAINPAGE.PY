import http.client
import json
import os
from termcolor import colored
import threading
import datetime


api_key = 'JcFG31W2RMZ0sAwzje27Aqc0l5lamutV'
state_area_codes = {
    'AL': ['205', '251', '256', '334', '938'],
    'AK': ['907'],
    'AZ': ['480', '520', '602', '623', '928'],
    'AR': ['479', '501', '870'],
    'CA': ['209', '213', '310', '323', '408', '415', '424', '442', '510', '530', '559', '562', '619', '626', '628', '650', '657', '661', '669', '707', '714', '747', '760', '805', '818', '831', '858', '909', '916', '925', '949', '951'],
    'CO': ['303', '719', '720', '970'],
    'CT': ['203', '475', '860', '959'],
    'DE': ['302'],
    'FL': ['239', '305', '321', '352', '386', '407', '561', '727', '754', '772', '786', '813', '850', '863', '904', '941', '954'],
    'GA': ['229', '404', '470', '478', '678', '706', '762', '770', '912'],
    'HI': ['808'],
    'ID': ['208'],
    'IL': ['217', '224', '309', '312', '331', '618', '630', '708', '773', '779', '815', '847'],
    'IN': ['219', '260', '317', '463', '574', '765', '812', '930'],
    'IA': ['319', '515', '563', '641', '712'],
    'KS': ['316', '620', '785', '913'],
    'KY': ['270', '364', '502', '606', '859'],
    'LA': ['225', '318', '337', '504', '985'],
    'ME': ['207'],
    'MD': ['240', '301', '410', '443', '667'],
    'MA': ['339', '351', '413', '508', '617', '774', '781', '857', '978'],
    'MI': ['231', '248', '269', '313', '517', '586', '616', '734', '810', '906', '947', '989'],
    'MN': ['218', '320', '507', '612', '651', '763', '952'],
    'MS': ['228', '601', '662', '769'],
    'MO': ['314', '417', '573', '636', '660', '816'],
    'MT': ['406'],
    'NE': ['308', '402', '531'],
    'NV': ['702', '725', '775'],
    'NH': ['603'],
    'NJ': ['201', '551', '609', '732', '848', '856', '862', '908', '973'],
    'NM': ['505', '575'],
    'NY': ['212', '315', '332', '347', '516', '518', '585', '607', '631', '646', '680', '716', '718', '845', '914', '917', '929', '934'],
    'NC': ['252', '336', '704', '743', '828', '910', '919', '980', '984'],
    'ND': ['701'],
    'OH': ['216', '220', '234', '330', '380', '419', '440', '513', '567', '614', '740', '937'],
    'OK': ['405', '539', '580', '918'],
    'OR': ['458', '503', '541', '971'],
    'PA': ['215', '267', '272', '412', '484', '570', '610', '717', '724', '814', '878'],
    'RI': ['401'],
    'SC': ['803', '843', '854', '864'],
    'SD': ['605'],
    'TN': ['423', '615', '629', '731', '865', '901', '931'],
    'TX': ['210', '214', '254', '281', '325', '346', '361', '409', '430', '432', '469', '512', '682', '713', '737', '806', '817', '830', '832', '903', '915', '936', '940', '956', '972', '979'],
    'UT': ['385', '435', '801'],
    'VT': ['802'],
    'VA': ['276', '434', '540', '571', '703', '757', '804'],
    'WA': ['206', '253', '360', '425', '509', '564'],
    'WV': ['304', '681'],
    'WI': ['262', '414', '534', '608', '715', '920'],
    'WY': ['307']
}

def validate_phone_number(api_key, phone_number):
    conn = http.client.HTTPSConnection("api.trestleiq.com")
    headers = {"Content-Type": "application/json"}
    params = f"?api_key={api_key}&phone={phone_number}"
    conn.request("GET", "/3.0/phone_intel" + params, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


def save_generated_numbers(numbers, name, folder):
    # Save generated numbers to a file
    filename = os.path.join(folder, f"{name}.txt")
    with open(filename, "w") as file:
        file.write("\n".join(numbers))


def validate_and_sort_numbers(numbers, name):
    results = {}
    lock = threading.Lock()  # Lock to ensure thread-safe writing to files and printing

    def process_number(number):
        response = validate_phone_number(api_key, number)
        carrier = response.get("carrier")
        is_valid = response.get("is_valid")

        if is_valid and carrier:
            with lock:
                if carrier not in results:
                    results[carrier] = []
                results[carrier].append(number)

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

    # Create a folder within the 'results' folder based on the current date
    now = datetime.now()
    folder_name = now.strftime("%Y-%m-%d")
    results_folder = os.path.join("results", folder_name)
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    # Save the validated and sorted numbers
    for carrier, carrier_numbers in results.items():
        save_generated_numbers(carrier_numbers, carrier, results_folder)

    print("Numbers sorted and saved successfully!")



def generate_numbers_by_state():
    # Logic for generating numbers by state
    state = input("Enter state abbreviation: ")
    area_codes = state_area_codes.get(state.upper(), [])
    if not area_codes:
        print("Invalid state abbreviation. Please try again.")
        return

    name = input("Enter a name to save the generated numbers: ")

    num_numbers = input("Enter the number of numbers to generate (1-5000): ")
    num_numbers = int(num_numbers)
    if num_numbers < 1 or num_numbers > 5000:
        print("Invalid number of numbers. Please try again.")
        return

    generated_numbers = []
    for area_code in area_codes:
        for i in range(num_numbers):
            number = f"{area_code}{i:07d}"
            generated_numbers.append(number)

    return generated_numbers, name


def generate_numbers_by_area_code():
    # Logic for generating numbers by area code
    area_code = input("Enter area code: ")
    if not area_code.isdigit():
        print("Invalid area code. Please enter a valid number.")
        return

    name = input("Enter a name to save the generated numbers: ")

    num_numbers = input("Enter the number of numbers to generate (1-5000): ")
    num_numbers = int(num_numbers)
    if num_numbers < 1 or num_numbers > 5000:
        print("Invalid number of numbers. Please try again.")
        return

    generated_numbers = []
    for i in range(num_numbers):
        number = f"{area_code}{i:07d}"
        generated_numbers.append(number)

    return generated_numbers, name


def generate_numbers_by_all_states():
    # Logic for generating numbers by all states
    name = input("Enter a name to save the generated numbers: ")

    num_numbers = input("Enter the number of numbers to generate (1-5000): ")
    num_numbers = int(num_numbers)
    if num_numbers < 1 or num_numbers > 5000:
        print("Invalid number of numbers. Please try again.")
        return

    generated_numbers = []
    for area_codes in state_area_codes.values():
        for area_code in area_codes:
            for i in range(num_numbers):
                number = f"{area_code}{i:07d}"
                generated_numbers.append(number)

    return generated_numbers, name


def main_menu():
    while True:
        print("Main Menu")
        print("1. Generate Numbers")
        print("2. Validate and Sort")
        choice = input("Enter your choice (1-2): ")

        if choice == "1":
            generate_numbers_submenu()
        elif choice == "2":
            validate_and_sort_numbers_menu()
        else:
            print("Invalid choice. Please try again.")


def generate_numbers_submenu():
    while True:
        print("\nGenerate Numbers Submenu")
        print("1. Generate Numbers by State")
        print("2. Generate Numbers by Area Code")
        print("3. Generate Numbers by ALL STATES")
        print("4. Back to Main Menu")
        choice = input("Enter your choice (1-4): ")

        if choice == "1":
            numbers, name = generate_numbers_by_state()
            save_generated_numbers(numbers, name)
        elif choice == "2":
            numbers, name = generate_numbers_by_area_code()
            save_generated_numbers(numbers, name)
        elif choice == "3":
            numbers, name = generate_numbers_by_all_states()
            save_generated_numbers(numbers, name)
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")


def validate_and_sort_numbers_menu():
    phone_numbers_file = input("Enter the file to import for validation and sorting: ")

    # Read phone numbers from file
    numbers = []
    with open(phone_numbers_file, "r") as file:
        for line in file:
            number = line.strip()
            numbers.append(number)

    name = input("Enter a name to save the validated and sorted numbers: ")

    validate_and_sort_numbers(numbers, name)


# Start the program
main_menu()