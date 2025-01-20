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
    
    # Add buttons for overall time frame selection (affects all charts)
    time_frame = st.radio(
        "Select Time Frame",
        ["Last Day", "Last Week", "Last Month", "Last Year", "Max"]
    )
    
    # Determine the start date based on the selected overall timeframe
    end_date = consumer_df['Datetime'].max()
    
    if time_frame == "Last Day":
        start_date = end_date - pd.Timedelta(days=1)
    elif time_frame == "Last Week":
        start_date = end_date - pd.Timedelta(weeks=1)
    elif time_frame == "Last Month":
        start_date = end_date - pd.Timedelta(days=30)
    elif time_frame == "Last Year":
        start_date = end_date - pd.Timedelta(days=365)
    elif time_frame == "Max":
        start_date = consumer_df['Datetime'].min()
    
    # Filter the consumer dataframe by the selected time period
    filtered_df = consumer_df[consumer_df['Datetime'] >= start_date]
    
    # Calculate cumulative measurements for the filtered data
    cumulative_df = calculate_cumulative(filtered_df, 'D')
    
    # Calculate rolling averages for the filtered data
    rolling_df = calculate_rolling_average(filtered_df, 'D')
    
    # Create a bar chart for cumulative measurements
    fig_cumulative = go.Figure()
    
    fig_cumulative.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Energy Consumption (Code 423)'], name='Energy Consumption (kWh)'))
    fig_cumulative.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Surplus Energy (Code 413)'], name='Surplus Energy (kWh)'))
    fig_cumulative.add_trace(go.Bar(x=cumulative_df['Datetime'], y=cumulative_df['Self-consumption through grid (Code 418)'], name='Self-consumption through grid (kWh)'))
    
    fig_cumulative.update_layout(title='Cumulative Energy Metrics', xaxis_title='Datetime', yaxis_title='kWh')
    
    st.plotly_chart(fig_cumulative)
    
    # Create a line chart for energy efficiency (Self-consumed vs. Total Consumption)
    fig_efficiency = go.Figure()
    
    fig_efficiency.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Self-consumption through grid (Code 418)'], mode='lines', name='Self-consumed Energy (kWh)', line=dict(color='green')))
    fig_efficiency.add_trace(go.Scatter(x=rolling_df['Datetime'], y=rolling_df['Energy Consumption (Code 423)'], mode='lines', name='Total Energy Consumption (kWh)', line=dict(color='blue', dash='dash')))
    
    fig_efficiency.update_layout(title='Energy Efficiency: Self-consumed vs. Total Consumption', xaxis_title='Datetime', yaxis_title='kWh')
    st.plotly_chart(fig_efficiency)
    
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
    estimated_cost = total_consumption * 0.2  # Assuming €0.2 per kWh (this value can be adjusted)
    
    st.metric("Total Energy Consumption (kWh)", total_consumption)
    st.metric("Self-consumption Rate", f"{self_consumption_rate:.2f}%")
    st.metric("Estimated Cost (€)", f"${estimated_cost:.2f}")
    
    # Buttons below the pie chart for changing the timeframe of the pie chart only
    st.subheader("Adjust Timeframe for Pie Chart")

    # Pie chart timeframe buttons
    pie_time_frame = st.radio(
        "Select Pie Chart Time Frame",
        ["Last Day", "Last Week", "Last Month", "Last Year", "Max"]
    )
    
    # Adjust the filtered dataframe for pie chart based on the selected timeframe
    if pie_time_frame == "Last Day":
        pie_start_date = end_date - pd.Timedelta(days=1)
    elif pie_time_frame == "Last Week":
        pie_start_date = end_date - pd.Timedelta(weeks=1)
    elif pie_time_frame == "Last Month":
        pie_start_date = end_date - pd.Timedelta(days=30)
    elif pie_time_frame == "Last Year":
        pie_start_date = end_date - pd.Timedelta(days=365)
    elif pie_time_frame == "Max":
        pie_start_date = consumer_df['Datetime'].min()
    
    # Filter the data for the pie chart timeframe
    pie_filtered_df = consumer_df[consumer_df['Datetime'] >= pie_start_date]
    
    # Create a pie chart with updated filtered data
    fig_pie = go.Figure(go.Pie(
        labels=["Self-consumption", "Grid Consumption", "Surplus Energy"],
        values=[ 
            pie_filtered_df['Self-consumption through grid (Code 418)'].sum(),
            pie_filtered_df['Energy Consumption (Code 423)'].sum() - pie_filtered_df['Self-consumption through grid (Code 418)'].sum(),
            pie_filtered_df['Surplus Energy (Code 413)'].sum()
        ],
        hole=0.3
    ))
    fig_pie.update_layout(title=f'Energy Source Breakdown ({pie_time_frame})')
    st.plotly_chart(fig_pie)



