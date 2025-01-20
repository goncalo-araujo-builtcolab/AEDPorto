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
    rolling_df = numeric_df.rolling(window=window).mean().dropna().reset_index()
    return rolling_df

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Energy Consumers"])

# Page: Energy Consumers
if page == "Energy Consumers":
    st.title("Energy Consumers")
    
    # Time frame selection
    time_frame = st.selectbox("Select Time Frame", ["30 min", "1 hour", "1 day", "1 week", "1 month", "1 year"])
    
    # Map time frame to resample frequency and rolling window size
    time_frame_mapping = {
        "30 min": '30T',
        "1 hour": '1H',
        "1 day": '1D',
        "1 week": '7D',
        "1 month": '30D',
        "1 year": '365D'
    }
    
    freq = time_frame_mapping[time_frame]
    
    # Filter data based on selected time frame
    end_date = consumer_df['Datetime'].max()
    if time_frame == "30 min":
        start_date = end_date - pd.Timedelta(minutes=30)
    elif time_frame == "1 hour":
        start_date = end_date - pd.Timedelta(hours=1)
    elif time_frame == "1 day":
        start_date = end_date - pd.Timedelta(days=1)
    elif time_frame == "1 week":
        start_date = end_date - pd.Timedelta(weeks=1)
    elif time_frame == "1 month":
        start_date = end_date - pd.Timedelta(days=30)
    elif time_frame == "1 year":
        start_date = end_date - pd.Timedelta(days=365)
    
    # Filter the consumer dataframe by the selected time period
    filtered_df = consumer_df[consumer_df['Datetime'] >= start_date]
    
    # Calculate cumulative measurements for the filtered data
    cumulative_df = calculate_cumulative(filtered_df, freq)
    
    # Calculate rolling averages for the filtered data
    rolling_df = calculate_rolling_average(filtered_df, freq)
    
    # Create a bar chart for cumulative measurements
    fig_cumulative = go.Figure()
    
    fig_cumulative.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Energy Consumption (Code 423)'], name='Energy Consumption (kWh)'))
    fig_cumulative.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Surplus Energy (Code 413)'], name='Surplus Energy (kWh)'))
    fig_cumulative.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Self-consumption through grid (Code 418)'], name='Self-consumption through grid (kWh)'))
    
    fig_cumulative.update_layout(title='Cumulative Energy Metrics', xaxis_title='Datetime', yaxis_title='kWh')
    
    st.plotly_chart(fig_cumulative)
    
    # Create a line chart for rolling averages
    fig_rolling = go.Figure()
    
    fig_rolling.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Energy Consumption (Code 423)'], mode='lines', name='Energy Consumption (kWh)'))
    fig_rolling.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Surplus Energy (Code 413)'], mode='lines', name='Surplus Energy (kWh)'))
    fig_rolling.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Self-consumption through grid (Code 418)'], mode='lines', name='Self-consumption through grid (kWh)'))
    
    fig_rolling.update_layout(title='Rolling Average Energy Metrics', xaxis_title='Datetime', yaxis_title='kWh')
    
    st.plotly_chart(fig_rolling)
    
    # Energy Source Breakdown (Donut chart) based on the filtered data
    fig_pie = go.Figure(go.Pie(
        labels=["Self-consumption", "Grid Consumption", "Surplus Energy"],
        values=[
            filtered_df['Self-consumption through grid (Code 418)'].sum(),
            filtered_df['Energy Consumption (Code 423)'].sum() - filtered_df['Self-consumption through grid (Code 418)'].sum(),
            filtered_df['Surplus Energy (Code 413)'].sum()
        ],
        hole=0.3
    ))
    fig_pie.update_layout(title=f'Energy Source Breakdown ({time_frame})')
    st.plotly_chart(fig_pie)
    
    # Display additional KPIs for energy efficiency and savings
    total_consumption = filtered_df['Energy Consumption (Code 423)'].sum()
    total_self_consumed = filtered_df['Self-consumption through grid (Code 418)'].sum()
    total_surplus = filtered_df['Surplus Energy (Code 413)'].sum()
    
    self_consumption_rate = (total_self_consumed / total_consumption) * 100 if total_consumption else 0
    estimated_cost = total_consumption * 0.12  # Assuming $0.12 per kWh (this value can be adjusted)
    
    st.metric("Total Energy Consumption (kWh)", total_consumption)
    st.metric("Self-consumption Rate", f"{self_consumption_rate:.2f}%")
    st.metric("Estimated Cost ($)", f"${estimated_cost:.2f}")
    
    # Display efficiency line chart for the selected timeframe
    fig_efficiency = go.Figure()
    
    fig_efficiency.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Self-consumption through grid (Code 418)'], mode='lines', name='Self-consumed Energy (kWh)', line=dict(color='green')))
    fig_efficiency.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Energy Consumption (Code 423)'], mode='lines', name='Total Energy Consumption (kWh)', line=dict(color='blue', dash='dash')))
    
    fig_efficiency.update_layout(title='Energy Efficiency: Self-consumed vs. Total Consumption', xaxis_title='Datetime', yaxis_title='kWh')
    st.plotly_chart(fig_efficiency)
    
    # Display raw data for the selected time period
    st.write(f"Here is the data for energy consumers for the last {time_frame}:")
    st.dataframe(filtered_df)


