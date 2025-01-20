# %%
import pandas as pd
import numpy as np  
import plotly.graph_objects as go
import streamlit as st

# %%
file_path = r"fullexcel.xlsx"
consumer_df = pd.read_excel(file_path, sheet_name="Consumer")  # Assuming tab-delimited
producer_df = pd.read_excel(file_path, sheet_name='Producer')  # Assuming tab-delimited

# %%
# Drop the last row from both DataFrames
producer_df = producer_df.drop(producer_df.index[-1])
consumer_df = consumer_df.drop(consumer_df.index[-1])

# %%
# Convert HH:MM to a proper time format
consumer_df['HH:MM'] = consumer_df['HH:MM'].astype(int)

# Convert HH:MM to a proper time format
def convert_time_format(x):
    hours = x // 100
    minutes = x % 100
    if hours == 24:
        hours = 0
        next_day = True
    else:
        next_day = False
    return f"{hours:02d}:{minutes:02d}", next_day

consumer_df['HH:MM'], consumer_df['Next_Day'] = zip(*consumer_df['HH:MM'].apply(convert_time_format))

# Combine Date and HH:MM into a single Datetime column
consumer_df['Datetime'] = pd.to_datetime(consumer_df['Date'].astype(str) + ' ' + consumer_df['HH:MM'], format='%Y%m%d %H:%M')

# Convert kW to kWh (since each row represents 15 minutes)
consumer_df['Surplus Energy (Code 413)'] /= 4
consumer_df['Imputed Energy (Code 415)'] /= 4
consumer_df['Self-consumption through grid (Code 418)'] /= 4
consumer_df['Energy Consumption (Code 423)'] /= 4
consumer_df = consumer_df.sort_values(by='Datetime')


# %%
# Convert HH:MM to a proper time format
producer_df['HH:MM'] = producer_df['HH:MM'].astype(int)


# Combine Date and HH:MM into a single Datetime column
producer_df['HH:MM'], producer_df['Next_Day'] = zip(*producer_df['HH:MM'].apply(convert_time_format))
producer_df['Datetime'] = pd.to_datetime(producer_df['Date'].astype(str) + ' ' + producer_df['HH:MM'], format='%Y%m%d %H:%M')

# Convert kW to kWh (since each row represents 15 minutes)
producer_df['Surplus Energy (Code 413)'] /= 4
producer_df['Imputed Energy (Code 415)'] /= 4
producer_df['Energy consumption (Code 423)'] /= 4
producer_df['Injected Energy per Energy Producer (Code 424)'] /= 4
producer_df = producer_df.sort_values(by='Datetime')


# %%
# Function to calculate cumulative measurements
def calculate_cumulative(df, freq):
    df = df.set_index('Datetime')
    numeric_df = df.select_dtypes(include=[np.number])
    cumulative_df = numeric_df.resample(freq).sum().cumsum().reset_index()
    return cumulative_df

# Function to calculate rolling averages
def calculate_rolling_average(df, window):
    df = df.set_index('Datetime')
    numeric_df = df.select_dtypes(include=[np.number])
    rolling_df = numeric_df.resample(window).mean().reset_index()
    return rolling_df

# %%


# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Energy Consumers", "Energy Producers"], )

# Page: Energy Consumers
if page == "Energy Consumers":
    st.title("Energy Consumers")
    
    # Time frame selection
    time_frame = st.selectbox("Select Time Frame", [ "30 min", "1 hour", "1 day", "1 week", "1 month", "1 year"])
    
    # Map time frame to rolling window size
    time_frame_mapping = {
        "30 min": '30T',
        "1 hour": '1H',
        "1 day": '1D',
        "1 week": '7D',
        "1 month": '30D',
        "1 year": '365D'
    }
    
    freq = time_frame_mapping[time_frame]
    
    # Calculate cumulative measurements
    cumulative_df = calculate_cumulative(consumer_df, freq)

    # Calculate rolling averages
    rolling_df = calculate_rolling_average(consumer_df, freq)

    
    # Create a combined Plotly line chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Self-consumption through grid (Code 418)'], name='Energy Consumption (kWh)'))
    fig.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Surplus Energy (Code 413)'], name='Surplus Energy (kWh)'))
    fig.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Energy Consumption (Code 423)'], name='Self-Consumption (kWh)'))
    
    fig.update_layout(title='Cumulative Energy Metrics', xaxis_title='Datetime', yaxis_title='kWh')
    
    st.plotly_chart(fig)

    # Create a line chart for rolling averages
    fig_rolling = go.Figure()

    fig.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Self-consumption through grid (Code 418)'], mode='lines', name='Self-Consumption (kWh)'))
    fig.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Surplus Energy (Code 413)'], mode='lines', name='Surplus Energy (kWh)'))
    fig.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Energy Consumption (Code 423)'], mode='lines', name='Energy Consumption (kWh)'))
    
    fig_rolling.update_layout(title='Rolling Average Energy Metrics', xaxis_title='Datetime', yaxis_title='kWh')
    
    st.plotly_chart(fig_rolling)
    
    # Display data
    st.write("Here is the data for energy consumers:")
    st.dataframe(consumer_df)



# %%



