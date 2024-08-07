import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
import time

# Load user credentials from secrets
def load_credentials():
    return st.secrets["users"]

# Check if the provided credentials are correct
def authenticate(username, password, credentials):
    return credentials.get(username) == password

# Main function to run the Streamlit app
def main():
    # Initialize session state for login status
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.show_success = False

    # Load credentials
    credentials = load_credentials()

    if not st.session_state.logged_in:
        st.title("Login")
        # Create login form
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate(username, password, credentials):
                st.session_state.logged_in = True
                st.session_state.show_success = True
                st.rerun()
            else:
                st.error("Invalid username or password")

    if st.session_state.logged_in:
        if st.session_state.show_success:
            st.success("Login successful!")
            time.sleep(3)
            st.session_state.show_success = False
            st.rerun()

        # Google Sheets connection and data display
        # Set page to always wide
        st.set_page_config(layout="wide")
        st.title("Fabric Analysis")

        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="DATA SALES CO & FABRIC", ttl=5)
        df = df.dropna(how="all")

        # st.dataframe(df)

        # Convert date column to datetime
        date_column = 'TIMESTAMP'
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

        delivery_date_column = 'DELIVERY PLAN DATE'
        df[delivery_date_column] = pd.to_datetime(df[delivery_date_column], errors='coerce')

        # Extract unique values
        df['month_year'] = df[date_column].dt.strftime('%b %Y')
        unique_months = df['month_year'].dropna().unique()
        unique_months = sorted(unique_months, key=lambda x: pd.to_datetime(x, format='%b %Y'), reverse=False)

        df['delivery_month_year'] = df[delivery_date_column].dt.strftime('%b %Y')
        unique_delivery_month = df['delivery_month_year'].dropna().unique()
        unique_delivery_month = sorted(unique_delivery_month, key=lambda x: pd.to_datetime(x, format='%b %Y'), reverse=False)

        unique_trip = df['TRIP'].dropna().unique()

        # Sidebar for month filter
        # st.sidebar.title("Filters")

        selected_months = st.sidebar.multiselect("Select Month(s) by Orders", unique_months, default=unique_months)
        selected_trip = st.sidebar.multiselect("Select Trip(s)", unique_trip, default=unique_trip)
        selected_delivery_months = st.sidebar.multiselect("Select Month(s) by Delivery", unique_delivery_month, default=unique_delivery_month)

        # Filter DataFrame by selected months
        filtered_df = df[df['month_year'].isin(selected_months)
                        & df['TRIP'].isin(selected_trip)
                        & df['delivery_month_year'].isin(selected_delivery_months)
                        ]

        # Display filtered DataFrame
        st.dataframe(filtered_df)



        usage, graph = st.columns(2)

        with usage:
            fabric_columns = [col for col in filtered_df.columns if 'FABRIC' in col]
            # fabric_columns

            qty_columns = [col for col in filtered_df.columns if 'QTY ' in col]
            # qty_columns

            unique_fabric = pd.Series(df[fabric_columns].values.ravel()).dropna().unique()
            # unique_fabric

            result_data = []

            for fabric in unique_fabric:
                total_value = 0 
                for fabric_col, qty_col in zip(fabric_columns, qty_columns):
                    fabric_mask = filtered_df[fabric_col] == fabric
                    qty_values = pd.to_numeric(filtered_df.loc[fabric_mask, qty_col], errors='coerce').dropna()
                    total_value += qty_values.sum()
                result_data.append({'FABRIC': fabric, 'USAGE BASED ON ORDERS': total_value})

            result_df = pd.DataFrame(result_data)
            result_df = result_df.sort_values(by='USAGE BASED ON ORDERS', ascending=False)

            st.subheader("Fabric Usage")
            result_df

        with graph:
            st.subheader("Fabric Usage by Month")
            selected_fabric = st.selectbox('Select Fabric: ', sorted(unique_fabric))

            fabric_usage_by_month = []

            for month in unique_months:
                month_df = filtered_df[filtered_df['month_year'] == month]
                total_value = 0
                for fabric_col, qty_col in zip(fabric_columns, qty_columns):
                    fabric_mask = month_df[fabric_col] == selected_fabric
                    qty_values = pd.to_numeric(month_df.loc[fabric_mask, qty_col], errors='coerce').dropna()
                    total_value += qty_values.sum()
                fabric_usage_by_month.append({'month_year': month, 'usage': total_value})

            fabric_usage_df = pd.DataFrame(fabric_usage_by_month)

            st.subheader(f"Fabric Usage of {selected_fabric} by Month")
            fig, ax = plt.subplots()
            ax.bar(fabric_usage_df['month_year'], fabric_usage_df['usage'])
            ax.set_xlabel("Month")
            ax.set_ylabel("Usage")
            ax.set_title(f"Usage of {selected_fabric} by Month")
            ax.grid(True)
            plt.xticks(rotation=45)
            st.pyplot(fig)

if __name__ == "__main__":
    main()