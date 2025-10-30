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
from back_end.report_objects.report_manager import ReportManager
from back_end.marathon_objects.marathon_plan_manager import MarathonPlan

# Configuration constants
WEEKS_FOR_WEEKLY_MILEAGE = 14

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
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Weekly Mileage", "🏆 Personal Records", "📝 Marathon Plan", "⚡ Pace Prediction"])
    
    with tab1:
        show_weekly_mileage_tab()
    
    with tab2:
        show_personal_records_tab()

    with tab3:
        show_marathon_plan_tab()

    with tab4:
        show_pace_prediction_tab()


def show_weekly_mileage_tab():
    st.header("📊 Weekly Mileage Analysis")
    
    start_date = datetime.now().date() - timedelta(weeks=WEEKS_FOR_WEEKLY_MILEAGE)
    end_date = datetime.now().date()    
    week_period = 7
    
    
    if st.button("Generate Weekly Mileage Report", type="primary"):
        with st.spinner("Fetching weekly mileage data..."):
            try:
                manager = ReportManager()
                stats = manager.get_activity_statistics(
                    client=st.session_state.garmin_client,
                    start_date=start_date,
                    end_date=end_date,
                    week_period_days=week_period,
                )
                weekly_data = stats['weekly_mileage']
                
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
                col1, = st.columns(1)
                
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
                
                # Data table
                st.subheader("📋 Weekly Mileage Data")
                st.dataframe(
                    weekly_data,
                    use_container_width=True,
                    hide_index=False
                )
                
            except Exception as e:
                st.error(f"Error fetching weekly mileage data: {str(e)}")

def show_personal_records_tab():
    st.header("🏆 Personal Records")
    
    if st.button("Load Personal Records", type="primary"):
        with st.spinner("Fetching personal records..."):
            try:
                manager = ReportManager()
                # Use same default range; dates unused for PRs
                stats = manager.get_activity_statistics(
                    client=st.session_state.garmin_client,
                    start_date=(datetime.now().date() - timedelta(weeks=WEEKS_FOR_WEEKLY_MILEAGE)),
                    end_date=datetime.now().date(),
                )
                pr_data = stats['personal_records']
                
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

def show_marathon_plan_tab():
    st.header("📝 Marathon Plan")
    report_mgr = ReportManager()
    plan_cls = MarathonPlan
    # --- 1. INITIALIZATION ---
    if 'mp_initialized' not in st.session_state:
        loaded = report_mgr.load_plan()
        
        if loaded is not None:
            name, start_d, race_d, df = loaded
            st.session_state.mp_name = name
            st.session_state.mp_start = start_d
            st.session_state.mp_race = race_d
            # Store RAW plan (no totals) in session state
            st.session_state.initial_df = df.copy()
        else:
            default_name = 'My Marathon Plan'
            default_start = datetime.now().date()
            default_race = (datetime.now().date() + timedelta(weeks=16))
            st.session_state.mp_name = default_name
            st.session_state.mp_start = default_start
            st.session_state.mp_race = default_race
            gen_df = plan_cls(default_name, default_start, default_race).df
            st.session_state.initial_df = gen_df.copy()

        st.session_state.mp_initialized = True
        
    # --- 2. PLAN METADATA INPUTS ---
    col1, col2, col3 = st.columns(3)

    with col1:
        # Plan selector
        existing_plans = ["<New Plan>"] + report_mgr.list_plans()
        default_plan = st.session_state.get('mp_selected_plan') or (existing_plans[1] if len(existing_plans) > 1 else existing_plans[0])
        selected_plan = st.selectbox("Plan", existing_plans, index=existing_plans.index(default_plan) if default_plan in existing_plans else 0)
        st.session_state.mp_selected_plan = None if selected_plan == "<New Plan>" else selected_plan
        name = st.text_input("Plan Name", value=st.session_state.mp_name)
    with col2:
        start_date = st.date_input("Start Date", value=st.session_state.mp_start, max_value=st.session_state.mp_race)
    with col3:
        race_date = st.date_input("Race Date", value=st.session_state.mp_race, min_value=st.session_state.mp_start)

    # Update session state with current inputs
    st.session_state.mp_name = name
    st.session_state.mp_start = start_date
    st.session_state.mp_race = race_date
    # --- 3. BUTTONS ---
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("Create/Reset Plan", type="primary"):
            gen_df = plan_cls(st.session_state.mp_name, st.session_state.mp_start, st.session_state.mp_race).df
            # Overwrite session state with new RAW plan data
            st.session_state.initial_df = gen_df.copy()
            st.session_state.edited_df = st.session_state.initial_df.copy()
    
    with c2:
        # Load selected plan (if changed)
        if st.button("Load Selected") and st.session_state.get('mp_selected_plan'):
            loaded = report_mgr.load_plan(st.session_state.mp_selected_plan)
            if loaded is not None:
                name, start_d, race_d, df = loaded
                st.session_state.mp_name = name
                st.session_state.mp_start = start_d
                st.session_state.mp_race = race_d
                st.session_state.initial_df = df.copy()
                st.session_state.edited_df = st.session_state.initial_df.copy()

    # --- 4. PLAN EDITOR ---
    st.subheader("Plan Editor")
    st.caption("Format each day as '#: Description' (e.g., '8: Easy'). Only the number before ':' is summed into Weekly Total.")
    
    # Ensure expected columns exist in state
    def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
        dfc = df.copy()
        expected = ['Week', 'First_Monday', *plan_cls.distance_columns(), *plan_cls.type_columns(), *plan_cls.notes_columns()]
        for col in expected:
            if col not in dfc.columns:
                if col.endswith('_Dist'):
                    dfc[col] = 0.0
                elif col.endswith('_Type'):
                    dfc[col] = plan_cls.RUN_TYPES[0]
                elif col.endswith('_Notes'):
                    dfc[col] = ''
        # Coerce dtypes to match editor configs
        for col in plan_cls.distance_columns():
            if col in dfc.columns:
                dfc[col] = pd.to_numeric(dfc[col], errors='coerce').fillna(0.0)
        for col in plan_cls.type_columns():
            if col in dfc.columns:
                dfc[col] = dfc[col].fillna(plan_cls.RUN_TYPES[0]).astype(str)
        for col in plan_cls.notes_columns():
            if col in dfc.columns:
                dfc[col] = dfc[col].fillna('').astype(str)
        return dfc[expected]

    st.session_state.initial_df = ensure_columns(st.session_state.initial_df)

    # Column configuration for Dist/Type/Notes per day
    day_column_config = {}
    for day in plan_cls.DAY_COLUMNS:
        day_column_config[f"{day}_Dist"] = st.column_config.NumberColumn(f"{day} Dist (mi)", min_value=0.0, step=0.1, format="%.1f")
        day_column_config[f"{day}_Type"] = st.column_config.SelectboxColumn(f"{day} Type", options=plan_cls.RUN_TYPES)
        day_column_config[f"{day}_Notes"] = st.column_config.TextColumn(f"{day} Notes")
    #print("Raw for editing: " + str(st.session_state.mp_plan_df_raw))
    # 1) Show RAW editor (no 'Weekly Total') and capture edits
    #st.session_state.raw_for_editing = st.session_state.mp_plan_df_raw
    
    edited_df = st.data_editor(
        st.session_state.initial_df,
        column_config=day_column_config,
        use_container_width=True,
        hide_index=True,
        disabled=["Week", "First_Monday"],
        key="mp_editor_raw",
    )
    st.session_state.edited_df = ensure_columns(edited_df)
    
    # Build totals and readable view
    totals_view_df = plan_cls.compute_weekly_totals_df(st.session_state.edited_df.copy())
    readable_df = plan_cls.build_readable_view(st.session_state.edited_df.copy())


    # Readable table
    st.subheader("Readable Plan")
    st.dataframe(readable_df, use_container_width=True, hide_index=True)

    # # 2) Persist RAW edits for the next run
    #st.session_state.mp_plan_df_raw = st.session_state.edited_df
    #print("Session state raw df: " + str(st.session_state.mp_plan_df_raw))
    # Save plan AFTER editor so it captures the updated edits
    if st.button("Save Plan", type="primary"):
        report_mgr.save_plan(
            st.session_state.mp_name,
            st.session_state.mp_start,
            st.session_state.mp_race,
            st.session_state.edited_df,
        )
        st.success("Plan saved")
        st.rerun()

def show_pace_prediction_tab():
    st.header("⚡ Pace Prediction")
    report_mgr = ReportManager()

    if 'garmin_client' not in st.session_state or st.session_state.garmin_client is None:
        st.info("👈 Please authenticate in the sidebar to use pace prediction.")
        return

    plans = report_mgr.list_plans()
    if not plans:
        st.info("No saved plans found. Save a plan in the Marathon Plan tab first.")
        return
    plan_name = st.selectbox("Plan", plans)
    loaded = report_mgr.load_plan(plan_name)
    if loaded is None:
        st.warning("Failed to load selected plan.")
        return
    name, start_d, race_d, df_plan = loaded
    # Build plan object for prediction
    plan_obj = MarathonPlan(name, start_d, race_d)
    plan_obj.from_dataframe(df_plan)


    # Determine today's planned run using the object model
    today_date = datetime.now().date()
    found = plan_obj._find_week_and_day_by_date(today_date)  # object lookup
    if not found:
        st.info("Today's date is not within the selected plan's range.")
        return
    week_obj, day_name, run_obj = found

    # Show planned run as metrics
    st.caption("Planned Run for Today")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📏 Distance (mi)", f"{run_obj.get_distance():.1f}")
    with c2:
        st.metric("🏷️ Type", str(run_obj.get_type()))
    with c3:
        st.metric("📅 Date", today_date.strftime('%Y-%m-%d'))
    if str(run_obj.get_notes()).strip():
        st.caption(f"📝 Notes: {run_obj.get_notes()}")

    if st.button("Predict Pace", type="primary"):
        run_date = today_date
        # Ensure model is trained once
        if getattr(report_mgr, 'pacing_model', None) is None:
            with st.spinner("Training model for prediction..."):
                report_mgr.train_pacing_model(st.session_state.garmin_client)
        with st.spinner("Predicting pace... may take 1-2 minutes"):
            result = plan_obj.predict_pace_for_run_date(
                client=st.session_state.garmin_client,
                run_date=pd.Timestamp(run_date).date(),
                model=report_mgr.pacing_model,
            )
        if result is None:
            st.warning("Skipped: Rest day, zero distance, or missing data.")
            return
        st.subheader("Prediction")
        # 1. Get the decimal pace
        decimal_pace = result['predicted_pace_min_per_mile']

        # 2. Calculate minutes and seconds
        minutes = int(decimal_pace)
        seconds = round((decimal_pace - minutes) * 60)
        st.metric("🔮 Predicted Pace (min/mi)", f"{minutes}:{seconds:02d}")

        # Show model inputs/predictors as metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("🌡️ Temperature (°F)", f"{result['temperature']}")
        with m2:
            st.metric("💧 Humidity (%)", f"{result['humidity']}")
        with m3:
            st.metric("💓 HRV (ms)", f"{result['hrv']}")
        with m4:
            st.metric("🫀 Resting HR (bpm)", f"{result['resting_heart_rate']}")

        m5, m6, m7 = st.columns(3)
        with m5:
            st.metric("📈 Days Since Start", f"{int(result['inputs']['days_since_start'])}")
        with m6:
            st.metric("⛰️ Elevation Gain (ft)", f"{int(result['inputs']['elevation_gain'])}")
        with m7:
            st.metric("🎯 Target HR (bpm)", f"{int(result['inputs']['avg_hr'])}")
        # Optional: show model analysis metrics in a dropdown
        with st.expander("📊 Model Metrics"):
            # Ensure model exists
            if getattr(report_mgr, 'pacing_model', None) is None:
                with st.spinner("Training model to compute metrics..."):
                    report_mgr.train_pacing_model(st.session_state.garmin_client)
            try:
                res = report_mgr.pacing_model.analyze_model()
                if len(res) == 5:
                    _, accuracy, coef_df, r2_train, r2_test = res  # ignore VIF
                else:
                    accuracy, coef_df, r2_train, r2_test = res
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("🎯 Accuracy (within 10s)", f"{accuracy}%")
                with m2:
                    st.metric("📈 R² Train", f"{r2_train:.3f}")
                with m3:
                    st.metric("🧪 R² Test", f"{r2_test:.3f}")
                st.caption("Standardized Coefficients")
                st.dataframe(coef_df, hide_index=True, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not compute metrics: {e}")

if __name__ == "__main__":
    main()
