# Garmin Performance Analysis - Streamlit Frontend

A beautiful web application for analyzing your Garmin Connect data, featuring weekly mileage tracking and personal records visualization.

## Features

### �� Weekly Mileage Analysis
- Interactive date range selection
- Customizable week periods (7, 10, or 14 days)
- Line and bar charts showing mileage trends
- Summary metrics (total miles, average, max)
- Detailed data table

### 🏆 Personal Records
- All-time personal records for 5K, 10K, Half Marathon, and Marathon
- Pace and time visualizations
- Color-coded charts for easy comparison
- Detailed records table

### 📝 Marathon Plan
- Create/load/save multiple named training plans
- Per-day fields: distance, type (Easy/Steady/Workout/Rest), notes
- Automatic weekly totals and readable plan view

### ⚡ Predictive Pace
- One-click pace prediction for today’s planned run
- Uses your plan, Garmin sleep/HR data, and local weather
- Shows predicted pace and key inputs (temp, humidity, HRV, resting HR)

## Setup

1. **Install Dependencies**
   ```bash
   # From the project root
   uv sync
   ```

2. **Environment Variables**
   Create a `.env` file in the project root with your Garmin credentials:
   ```bash
   GARMIN_EMAIL=your_email@example.com
   GARMIN_PASSWORD=your_password
   GARMINTOKENS=~/.garminconnect
   ```

3. **Run the Application**
   ```bash
   # From the project root
   streamlit run front_end/app.py
   ```

   Or from the front_end directory:
   ```bash
   cd front_end
   streamlit run app.py
   ```

## Usage

1. **Authentication**: Click "Connect to Garmin" in the sidebar to authenticate with your Garmin Connect account
2. **Weekly Mileage**: Select date ranges and week periods to analyze your running mileage
3. **Personal Records**: View your all-time personal records with visual comparisons
4. **Marathon Plan**: Build or load a plan, edit daily distance/type/notes, and save
5. **Pace Prediction**: Open the Pace tab and click Predict to get today’s expected pace

## Technical Details

- **Backend**: Python with garminconnect library
- **Frontend**: Streamlit with Plotly charts
- **Authentication**: Persistent session management with garth
- **Data Processing**: Pandas for data manipulation and analysis

## Troubleshooting

- **Authentication Issues**: Make sure your Garmin credentials are correct in the `.env` file
- **No Data**: Ensure you have running activities in the selected date range
- **Connection Errors**: Check your internet connection and Garmin Connect status

## Features in Detail

### Weekly Mileage Tab
- **Date Range Picker**: Select any date range for analysis
- **Week Period**: Choose how many days constitute a "week" (7, 10, or 14 days)
- **Visualizations**: 
  - Line chart showing mileage trends over time
  - Bar chart for week-to-week comparison
- **Metrics**: Total miles, average per week, maximum weekly mileage
- **Data Table**: Detailed breakdown of each week

### Personal Records Tab
- **Automatic Loading**: Fetches your latest PRs from Garmin Connect
- **Distance Coverage**: 5K, 10K, Half Marathon, Marathon
- **Visualizations**:
  - Pace comparison across distances
  - Time comparison across distances
- **Metrics**: Total PRs, fastest pace, longest distance

### Marathon Plan Tab
- **Plan Editor**: Edit daily distance, type, and notes (per week)
- **Weekly Totals**: Auto-summed from daily distance fields
- **Readable View**: Human-friendly plan table for quick review
- **Persistence**: Save/load named plans in the app

### Pace Prediction Tab
- **Today’s Run**: Automatically picks today’s planned run from your current plan
- **Prediction**: Uses Garmin sleep/resting HR and local weather
- **Outputs**: Predicted pace (min/mi) and metrics for temp, humidity, HRV, resting HR, etc.

## Customization

The application is built with modularity in mind. You can easily:
- Add new chart types in the visualization functions
- Modify the date range defaults
- Add new metrics or calculations
- Customize the styling and layout
