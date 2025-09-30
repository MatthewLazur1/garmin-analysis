import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add the back-end directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'back_end'))

from back_end.report_objects.report_reader import ReportReader
from back_end.report_objects.report_builder import ReportBuilder

# Page configuration
st.set_page_config(
    page_title="Garmin Performance Analysis",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🏃‍♂️ Garmin Performance Analysis</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'garmin_client' not in st.session_state:
        st.session_state.garmin_client = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    # Sidebar for authentication
    with st.sidebar:
        st.header("🔐 Authentication")
        
        if st.session_state.garmin_client is None:
            st.info("Please authenticate with Garmin Connect to view your data.")
            
            if st.button("Connect to Garmin", type="primary"):
                with st.spinner("Connecting to Garmin Connect..."):
                    try:
                        reader = ReportReader()
                        client = reader.fetch_garmin_data()
                        st.session_state.garmin_client = client
                        st.session_state.user_name = client.display_name
                        st.success(f"Connected as {client.display_name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to connect: {str(e)}")
        else:
            st.success(f"Connected as {st.session_state.user_name}")
            if st.button("Disconnect"):
                st.session_state.garmin_client = None
                st.session_state.user_name = None
                st.rerun()
    
    # Main content
    if st.session_state.garmin_client is None:
        st.info("👈 Please authenticate in the sidebar to view your Garmin data.")
        return
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Weekly Mileage", "🏆 Personal Records", "📈 Combined Analysis"])
    
    with tab1:
        show_weekly_mileage_tab()
    
    with tab2:
        show_personal_records_tab()
    
    with tab3:
        show_combined_analysis_tab()

def show_weekly_mileage_tab():
    st.header("📊 Weekly Mileage Analysis")
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=90),
            max_value=datetime.now()
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    # Week period selector
    week_period = st.selectbox(
        "Week Period (days)",
        options=[7, 10, 14],
        index=0,
        help="Number of days to group activities into weekly periods"
    )
    
    if st.button("Generate Weekly Mileage Report", type="primary"):
        with st.spinner("Fetching weekly mileage data..."):
            try:
                builder = ReportBuilder()
                weekly_data = builder.aggregate_weekly_mileage(
                    st.session_state.garmin_client,
                    start_date,
                    end_date,
                    week_period
                )
                
                if weekly_data.empty:
                    st.warning("No running activities found in the selected date range.")
                    return
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Weeks",
                        len(weekly_data),
                        help="Number of weeks with running activities"
                    )
                
                with col2:
                    total_miles = weekly_data['Total_Miles'].sum()
                    st.metric(
                        "Total Miles",
                        f"{total_miles:.1f}",
                        help="Total miles across all weeks"
                    )
                
                with col3:
                    avg_miles = weekly_data['Total_Miles'].mean()
                    st.metric(
                        "Avg Miles/Week",
                        f"{avg_miles:.1f}",
                        help="Average miles per week"
                    )
                
                with col4:
                    max_miles = weekly_data['Total_Miles'].max()
                    st.metric(
                        "Max Miles/Week",
                        f"{max_miles:.1f}",
                        help="Highest weekly mileage"
                    )
                
                # Create visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Line chart
                    fig_line = px.line(
                        weekly_data.reset_index(),
                        x='week_start',
                        y='Total_Miles',
                        title='Weekly Mileage Trend',
                        labels={'Total_Miles': 'Miles', 'week_start': 'Week'},
                        markers=True
                    )
                    fig_line.update_layout(
                        xaxis_title="Week",
                        yaxis_title="Miles",
                        height=400
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                
                with col2:
                    # Bar chart
                    fig_bar = px.bar(
                        weekly_data.reset_index(),
                        x='week_start',
                        y='Total_Miles',
                        title='Weekly Mileage Comparison',
                        labels={'Total_Miles': 'Miles', 'week_start': 'Week'}
                    )
                    fig_bar.update_layout(
                        xaxis_title="Week",
                        yaxis_title="Miles",
                        height=400
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                # Data table
                st.subheader("📋 Weekly Mileage Data")
                st.dataframe(
                    weekly_data,
                    use_container_width=True,
                    hide_index=True
                )
                
            except Exception as e:
                st.error(f"Error fetching weekly mileage data: {str(e)}")

def show_personal_records_tab():
    st.header("🏆 Personal Records")
    
    if st.button("Load Personal Records", type="primary"):
        with st.spinner("Fetching personal records..."):
            try:
                builder = ReportBuilder()
                pr_data = builder.get_all_time_prs(st.session_state.garmin_client)
                
                if pr_data.empty:
                    st.warning("No personal records found.")
                    return
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Total PRs",
                        len(pr_data),
                        help="Number of personal records"
                    )
                
                with col2:
                    # Find fastest pace
                    fastest_pace = pr_data['Pace'].iloc[0] if not pr_data.empty else "N/A"
                    st.metric(
                        "Fastest Pace",
                        fastest_pace,
                        help="Fastest pace across all distances"
                    )
                
                with col3:
                    # Find longest distance
                    longest_distance = pr_data['Distance'].iloc[-1] if not pr_data.empty else "N/A"
                    st.metric(
                        "Longest Distance",
                        longest_distance,
                        help="Longest distance with a PR"
                    )
                
                # Create visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pace comparison chart
                    fig_pace = px.bar(
                        pr_data,
                        x='Distance',
                        y='Pace',
                        title='Personal Record Paces',
                        color='Distance',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_pace.update_layout(
                        xaxis_title="Distance",
                        yaxis_title="Pace (min/mile)",
                        height=400
                    )
                    st.plotly_chart(fig_pace, use_container_width=True)
                
                with col2:
                    # Time comparison chart
                    # Convert time to minutes for plotting
                    pr_data_copy = pr_data.copy()
                    pr_data_copy['Time_Minutes'] = pr_data_copy['Time'].apply(
                        lambda x: sum(int(i) * 60**j for j, i in enumerate(reversed(x.split(':'))))
                    )
                    
                    fig_time = px.bar(
                        pr_data_copy,
                        x='Distance',
                        y='Time_Minutes',
                        title='Personal Record Times',
                        color='Distance',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_time.update_layout(
                        xaxis_title="Distance",
                        yaxis_title="Time (minutes)",
                        height=400
                    )
                    st.plotly_chart(fig_time, use_container_width=True)
                
                # Data table
                st.subheader("📋 Personal Records Data")
                st.dataframe(
                    pr_data,
                    use_container_width=True,
                    hide_index=True
                )
                
            except Exception as e:
                st.error(f"Error fetching personal records: {str(e)}")

def show_combined_analysis_tab():
    st.header("📈 Combined Analysis")
    
    st.info("This tab combines weekly mileage and personal records data for comprehensive analysis.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date for Mileage",
            value=datetime.now() - timedelta(days=90),
            max_value=datetime.now(),
            key="combined_start"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date for Mileage",
            value=datetime.now(),
            max_value=datetime.now(),
            key="combined_end"
        )
    
    if st.button("Generate Combined Analysis", type="primary"):
        with st.spinner("Generating combined analysis..."):
            try:
                builder = ReportBuilder()
                
                # Get both datasets
                weekly_data = builder.aggregate_weekly_mileage(
                    st.session_state.garmin_client,
                    start_date,
                    end_date
                )
                
                pr_data = builder.get_all_time_prs(st.session_state.garmin_client)
                
                if weekly_data.empty and pr_data.empty:
                    st.warning("No data available for analysis.")
                    return
                
                # Summary statistics
                st.subheader("📊 Summary Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if not weekly_data.empty:
                        total_miles = weekly_data['Total_Miles'].sum()
                        st.metric("Total Miles", f"{total_miles:.1f}")
                    else:
                        st.metric("Total Miles", "N/A")
                
                with col2:
                    if not weekly_data.empty:
                        avg_miles = weekly_data['Total_Miles'].mean()
                        st.metric("Avg Miles/Week", f"{avg_miles:.1f}")
                    else:
                        st.metric("Avg Miles/Week", "N/A")
                
                with col3:
                    if not pr_data.empty:
                        st.metric("Personal Records", len(pr_data))
                    else:
                        st.metric("Personal Records", "N/A")
                
                with col4:
                    if not pr_data.empty:
                        fastest_pace = pr_data['Pace'].iloc[0]
                        st.metric("Fastest Pace", fastest_pace)
                    else:
                        st.metric("Fastest Pace", "N/A")
                
                # Combined visualization
                if not weekly_data.empty:
                    st.subheader("📈 Weekly Mileage Trend")
                    fig = px.line(
                        weekly_data.reset_index(),
                        x='week_start',
                        y='Total_Miles',
                        title='Weekly Mileage Over Time',
                        labels={'Total_Miles': 'Miles', 'week_start': 'Week'},
                        markers=True
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data tables side by side
                if not weekly_data.empty or not pr_data.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if not weekly_data.empty:
                            st.subheader("📊 Weekly Mileage")
                            st.dataframe(weekly_data, use_container_width=True, hide_index=True)
                    
                    with col2:
                        if not pr_data.empty:
                            st.subheader("🏆 Personal Records")
                            st.dataframe(pr_data, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"Error generating combined analysis: {str(e)}")

if __name__ == "__main__":
    main()
