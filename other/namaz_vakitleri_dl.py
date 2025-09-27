import pandas as pd
from bs4 import BeautifulSoup
import requests
import os
import time


# Function to scrape and append data to a CSV file
def scrape_and_append_to_csv(choosed_city, csv_path, month):
    # Set parameters
    year = 2025  # Replace with the actual year
    lang = 'de'  # Replace with the actual language code

    # Set the AJAX endpoint URL
    url = "https://www.igmg.org/wp-content/themes/igmg/include/gebetskalender_ajax_api.php"

    # Set the data payload
    payload = {
        'show_ajax_variable': choosed_city,
        'show_month': month,
        'show_year': year,
        'lang': lang
    }

    # Set headers to mimic the X-Requested-With header
    headers = {'X-Requested-With': 'XMLHttpRequest'}

    # Make the POST request
    response = requests.post(url, data=payload, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the relevant section
        zeiten_box = soup.find('div', class_='zeiten_box')

        # Initialize an empty list to store DataFrames
        df_list = []

        # Iterate through each row
        for zeiten in zeiten_box.find_all('div', class_='zeiten'):
            # Extract date from the span with class 'date'
            date = zeiten.find('span', class_='tarih').text.strip()

            # Extract time_values from the corresponding spans with multiple classes
            time_values_classes = ['imsak_time', 'gunes_time', 'ogle_time', 'ikindi_time', 'aksam_time', 'yatsi_time']
            time_values = [span.text.strip() for span in zeiten.find_all('span', class_=time_values_classes)]

            # Create a DataFrame for the current row
            row_df = pd.DataFrame({'Tarih': [date], 'Imsak': [time_values[0]],
                                   'Günes': [time_values[1]], 'Ögle': [time_values[2]],
                                   'Ikindi': [time_values[3]], 'Aksam': [time_values[4]],
                                   'Yatsi': [time_values[5]]})

            # Append the DataFrame to the list
            df_list.append(row_df)

        # Concatenate the list of DataFrames into a single DataFrame
        final_df = pd.concat(df_list, ignore_index=True)

        # Convert the 'Tarih' column to datetime format with errors='coerce' to handle invalid dates
        final_df['Tarih'] = pd.to_datetime(final_df['Tarih'], format='%d.%m.%Y', errors='coerce').dt.strftime(
            '%d.%m.%Y')

        # Drop rows with invalid dates
        final_df = final_df.dropna(subset=['Tarih'])

        # Save the DataFrame to a CSV file for each loop iteration
        final_df.to_csv(csv_path, mode='a', header=False, index=False)

    else:
        print(f"Error: {response.status_code} - {response.text}")


# Path to the CSV file
csv_file_path = r'C:\Users\HOME\PycharmProjects\ign_rpi\raw_data\namaz_vakitleri_hamburg.csv'
print(csv_file_path)
# Check if the file exists and delete it
if os.path.exists(csv_file_path):
    os.remove(csv_file_path)

# Loop 12 times and append data to the CSV file with a 3-second delay
for i in range(1, 13):
    chosen_city = 20083
    scrape_and_append_to_csv(chosen_city, csv_file_path, i)

    # Introduce a 2-second delay
    time.sleep(2)
print("test")
# adding header to csv file since the header was deleted during date error check above
header_row = ['Tarih', 'İmsak', 'Güneş', 'Öğle', 'İkindi', 'Akşam', 'Yatsı']
df = pd.read_csv(csv_file_path, header=None)
df.columns = header_row
df.to_csv(csv_file_path, index=False)