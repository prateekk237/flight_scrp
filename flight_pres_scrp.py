import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

# streamlit flight UI
import streamlit as st
import datetime

from pygments.lexer import default

st.title("Precision Air Flight Search")
# Sidebar filters
trip_type = st.sidebar.selectbox("Trip Type", ["One Way", "Round Trip"])
dep_port = st.sidebar.text_input("Departure Airport (e.g., DAR)", "DAR")
arr_port = st.sidebar.text_input("Arrival Airport (e.g., ARK)", "ARK")
# Departure date
departure_date = st.sidebar.date_input("Departure Date", datetime.date.today())
formatted_departure_date = departure_date.strftime("%d/%m/%Y")

# Return date (only if round trip)
formatted_return_date = ""  # Initialize as empty string
if trip_type == "Round Trip":
    return_date = st.sidebar.date_input("Return Date", departure_date + datetime.timedelta(days=1))
    formatted_return_date = return_date.strftime("%d/%m/%Y")
# Gender column
adults = st.sidebar.number_input("Adults", min_value=1, value=1)
childs = st.sidebar.number_input("Child", min_value=0, value=0)
infant = st.sidebar.number_input("Infant", min_value=0, value=0)

# Build URL based on parameters
base_url = "https://book-precision.crane.aero/ibe/availability?"
params = {
            "tripType": "ONE_WAY" if trip_type == 'One Way' else "ROUND_TRIP",
            "depPort": dep_port,
            "arrPort": arr_port,
            "departureDate": formatted_departure_date,
            "returnDate": formatted_return_date,  # Include return date if provided
            "passengerQuantities[0][passengerType]": "ADLT",
            "passengerQuantities[0][quantity]": str(adults),
            "passengerQuantities[1][passengerType]": "CHILD",
            "passengerQuantities[1][quantity]": str(childs),  # Set child and infant to 0 for now
            "passengerQuantities[2][passengerType]": "INFT",
            "passengerQuantities[2][quantity]": str(infant),
            "currency": "USD",
            "lang": "en",
        }

# scraping site
def scrape_site_without_proxy(website):
    # scraping without proxy
    url = requests.get(website, verify=False)
    if url.status_code == 200:
        print('Collecting the Data for Scraping...')
        content = url.content

        # Create BeautifulSoup object
        soup = BeautifulSoup(content, 'html.parser')
        departure_times = []
        arrival_times = []
        flight_numbers = []
        durations = []
        total_stops = []
        prices = []

        # Find all flight details sections
        flight_details = soup.find_all(class_='info-row col-12')

        # Find all price sections
        price_sections = soup.find_all(class_='fare-container col-12 col-lg-8 col-xl-8')

        # Ensure flight details and price sections have the same length
        min_len = min(len(flight_details), len(price_sections))

        for i in range(min_len):
            flight_detail = flight_details[i]
            price_section = price_sections[i]


            # Extract flight number
            flight_no = flight_detail.find(class_='flight-no').text.strip()
            flight_numbers.append(flight_no)

            # Extract duration
            duration = flight_detail.find(class_='flight-duration').text.strip()
            durations.append(duration)

            # Extract total stops
            total_stop = flight_detail.find(class_='total-stop').text.strip()
            total_stops.append(total_stop)

            # Extract departure and arrival times
            times = flight_detail.find_all("span", attrs={'class': 'time'})
            departure_times.append(times[0].text)
            arrival_times.append(times[1].text)

            # Extract Price from the price section
            price_element = price_section.find(class_='offer-info-block cabin-name-PROMOTION')
            price = price_element.text.strip() if price_element else "No Seats"

            # Remove newline characters and extra spaces using regular expression
            price = re.sub(r'\s+', ' ', price).strip()
            prices.append(price)

        # Set display options for columns and fields
        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.width', None)
        # Create the Dataframe
        df = pd.DataFrame(
            {
            'From': formatted_departure_date + ' ' + dep_port,
            'To': formatted_return_date + ' ' +arr_port,
            'Departure Time': departure_times,
            'Arrival Time': arrival_times,
            'Flight no': flight_numbers,
            'Duration': durations,
            'Total Stops': total_stops,
            'Lowest Fare Details': prices
        })
        return df  # Return the DataFrame

    else:
        #print(f"Failed to retrieve data. Status code: {url.status_code}")
        return None  # Return None in case of error



# Generate URL with parameters
full_url = base_url + "&".join([f"{k}={v}" for k, v in params.items()])

# Display URL
#st.write("**Generated URL:**", full_url)

# Scrape data and display results
if st.button("Search Flights"):
    df = scrape_site_without_proxy(full_url)
    if df is not None:
        st.dataframe(df)
    else:
        st.error("Failed to retrieve flight data. Please check the URL and try again.")

#website = "https://book-precision.crane.aero/ibe/availability?tripType=ONE_WAY&depPort=DAR&arrPort=ARK&departureDate=11%2F10%2F2024&returnDate=&passengerQuantities%5B0%5D%5BpassengerType%5D=ADLT&passengerQuantities%5B0%5D%5BpassengerSubType%5D=&passengerQuantities%5B0%5D%5Bquantity%5D=1&passengerQuantities%5B1%5D%5BpassengerType%5D=CHLD&passengerQuantities%5B1%5D%5BpassengerSubType%5D=&passengerQuantities%5B1%5D%5Bquantity%5D=0&passengerQuantities%5B2%5D%5BpassengerType%5D=INFT&passengerQuantities%5B2%5D%5BpassengerSubType%5D=&passengerQuantities%5B2%5D%5Bquantity%5D=0&currency=USD&cabinClass=&lang=en&nationality=&promoCode=&accountCode=&affiliateCode=&clickId=&withCalendar=&isMobileCalendar=&market=&isFFPoint=false"
#print(scrape_site_without_proxy(website))


