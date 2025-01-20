import pandas as pd
import numpy as np  
import plotly.graph_objects as go
import streamlit as st

# Load the consumer and producer data
file_path = r"fullexcel.xlsx"
consumer_df = pd.read_excel(file_path, sheet_name="Consumer")
producer_df = pd.read_excel(file_path, sheet_name='Producer')

# Drop the last row from both DataFrames
producer_df = producer_df.drop(producer_df.index[-1])
consumer_df = consumer_df.drop(consumer_df.index[-1])

# Convert HH:MM to a proper time format for both consumer and producer data
def convert_time_format(x):
    hours = x // 100
    minutes = x % 100
    return f"{hours:02d}:{minutes:02d}"

consumer_df['HH:MM'] = consumer_df['HH:MM'].astype(int).apply(convert_time_format)
consumer_df['Datetime'] = pd.to_datetime(consumer_df['Date'].astype(str) + ' ' + consumer_df['HH:MM'], format='%Y%m%d %H:%M')
consumer_df = consumer_df.sort_values(by='Datetime')

producer_df['HH:MM'] = producer_df['HH:MM'].astype(int).apply(convert_time_format)
producer_df['Datetime'] = pd.to_datetime(producer_df['Date'].astype(str) + ' ' + producer_df['HH:MM'], format='%Y%m%d %H:%M')
producer_df = producer_df.sort_values(by='Datetime')

# Convert kW to kWh for 15-minute intervals
kwh_columns_consumer = ['Surplus Energy (Code 413)', 'Imputed Energy (Code 415)', 'Self-consumption through grid (Code 418)', 'Energy Consumption (Code 423)']
kwh_columns_producer = ['Surplus Energy (Code 413)', 'Imputed Energy (Code 415)', 'Energy consumption (Code 423)', 'Injected Energy per Energy Producer (Code 424)']

consumer_df[kwh_columns_consumer] = consumer_df[kwh_columns_consumer] / 4
producer_df[kwh_columns_producer] = producer_df[kwh_columns_producer] / 4

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
page = st.sidebar.radio("Go to", ["Energy Consumers", "Energy Producers"])

# Page: Energy Producers
if page == "Energy Producers":
    st.title("Energy Producers")

    # Time frame selection for producers
    producer_time_frame = st.radio(
        "Select Time Frame",
        ["Last Day", "Last Week", "Last Month", "Last Year", "Max"]
    )

    # Determine the start date based on the selected timeframe
    producer_end_date = producer_df['Datetime'].max()

    if producer_time_frame == "Last Day":
        producer_start_date = producer_end_date - pd.Timedelta(days=1)
    elif producer_time_frame == "Last Week":
        producer_start_date = producer_end_date - pd.Timedelta(weeks=1)
    elif producer_time_frame == "Last Month":
        producer_start_date = producer_end_date - pd.Timedelta(days=30)
    elif producer_time_frame == "Last Year":
        producer_start_date = producer_end_date - pd.Timedelta(days=365)
    elif producer_time_frame == "Max":
        producer_start_date = producer_df['Datetime'].min()

    # Filter the producer dataframe by the selected time period
    producer_filtered_df = producer_df[producer_df['Datetime'] >= producer_start_date]

    # Calculate cumulative energy production for the filtered producer data
    producer_cumulative_df = calculate_cumulative(producer_filtered_df, 'D')

    # Create a breakdown bar chart for energy metrics
    fig_breakdown = go.Figure()
    fig_breakdown.add_trace(go.Bar(
        x=producer_cumulative_df['Datetime'], 
        y=producer_cumulative_df['Injected Energy per Energy Producer (Code 424)'], 
        name='Injected Energy (kWh)', 
        marker_color='blue'
    ))
    fig_breakdown.add_trace(go.Bar(
        x=producer_cumulative_df['Datetime'], 
        y=producer_cumulative_df['Surplus Energy (Code 413)'], 
        name='Surplus Energy (kWh)', 
        marker_color='orange'
    ))
    fig_breakdown.add_trace(go.Bar(
        x=producer_cumulative_df['Datetime'], 
        y=producer_cumulative_df['Imputed Energy (Code 415)'], 
        name='Imputed Energy (kWh)', 
        marker_color='green'
    ))
    fig_breakdown.update_layout(
        barmode='stack',
        title='Energy Breakdown by Metric',
        xaxis_title='Datetime',
        yaxis_title='kWh'
    )
    st.plotly_chart(fig_breakdown)

    # Calculate additional KPIs
    total_injected_energy = producer_filtered_df['Injected Energy per Energy Producer (Code 424)'].sum()
    total_surplus_energy = producer_filtered_df['Surplus Energy (Code 413)'].sum()
    total_imputed_energy = producer_filtered_df['Imputed Energy (Code 415)'].sum()
    total_energy_production = total_injected_energy + total_surplus_energy + total_imputed_energy

    energy_production_efficiency = (total_injected_energy / total_energy_production) * 100 if total_energy_production else 0

    # Display KPIs
    st.metric("Total Injected Energy (kWh)", f"{total_injected_energy:.2f}")
    st.metric("Total Surplus Energy (kWh)", f"{total_surplus_energy:.2f}")
    st.metric("Total Imputed Energy (kWh)", f"{total_imputed_energy:.2f}")
    st.metric("Energy Production Efficiency", f"{energy_production_efficiency:.2f}%")

    # Pie chart for production breakdown
    fig_pie_production = go.Figure(go.Pie(
        labels=["Injected Energy", "Surplus Energy", "Imputed Energy"],
        values=[
            total_injected_energy,
            total_surplus_energy,
            total_imputed_energy
        ],
        hole=0.4
    ))
    fig_pie_production.update_layout(title="Energy Production Breakdown")
    st.plotly_chart(fig_pie_production)
