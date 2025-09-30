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

### 📈 Combined Analysis
- Integrated view of both mileage and PR data
- Summary statistics dashboard
- Side-by-side data tables
- Comprehensive performance overview

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
   streamlit run front-end/app.py
   ```

   Or from the front-end directory:
   ```bash
   cd front-end
   streamlit run app.py
   ```

## Usage

1. **Authentication**: Click "Connect to Garmin" in the sidebar to authenticate with your Garmin Connect account
2. **Weekly Mileage**: Select date ranges and week periods to analyze your running mileage
3. **Personal Records**: View your all-time personal records with visual comparisons
4. **Combined Analysis**: Get a comprehensive view of both datasets

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

### Combined Analysis Tab
- **Integrated Dashboard**: Summary of both datasets
- **Comprehensive Metrics**: All key statistics in one place
- **Side-by-Side Tables**: Compare weekly mileage and PR data
- **Trend Analysis**: See how your training correlates with performance

## Customization

The application is built with modularity in mind. You can easily:
- Add new chart types in the visualization functions
- Modify the date range defaults
- Add new metrics or calculations
- Customize the styling and layout
