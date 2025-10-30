import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime, date
from statsmodels.stats.outliers_influence import variance_inflation_factor

# --- 1. DEFINE CLASS FOR MODEL MANAGEMENT ---

class PredictivePacingModel:
    """
    Manages the training, scaling, and prediction of the running pace model.
    """
    def __init__(self):
        # The 8 predictors (X) we will use for the final prediction
        self.predictors = [
            'distance_miles', 
            'avg_hr', 
            'temperature', 
            'hrv',   
            'days_since_start',
            'elevation_gain',
            'resting_heart_rate',
            'humidity'
        ]
        self.target = 'pace'
        self.model = None
        self.scaler_X = None
        self.scaler_Y = None
        self.df = None
        self.X = None
        self.Y = None
        self.X_scaled = None
        self.Y_scaled = None
        self.model_X_train = None
        self.model_X_test = None
        self.model_Y_train = None
        self.model_Y_test = None
        # Initialized for safety
        self.MARGIN_SECONDS = 15
        self.MARGIN_MINUTES = self.MARGIN_SECONDS / 60

    def train_model(self, df: pd.DataFrame):
        """Trains the MLR model and saves the scalers."""
        
        # --- Store the original DataFrame reference ---
        self.df = df.copy() 
        # Define all columns necessary for the model (Predictors + Target)
        required_cols = self.predictors + [self.target]
        
        # --- ROBUST FIX: Handle Missing and Non-Finite Values ---
        df = df[required_cols].copy()
        df = df.dropna(subset=required_cols)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()
        
        # Separate features (X) and target (Y) from the cleaned DataFrame
        self.X = df[self.predictors]
        self.Y = df[[self.target]]

        # --- Standardization (Essential for fair comparison and prediction) ---
        self.scaler_X = StandardScaler()
        self.scaler_Y = StandardScaler()
        
        self.X_scaled = self.scaler_X.fit_transform(self.X)
        self.Y_scaled = self.scaler_Y.fit_transform(self.Y)
        
        # --- Split data for robust testing (80% Train, 20% Test) ---
        self.model_X_train, self.model_X_test, self.model_Y_train, self.model_Y_test = train_test_split(
            self.X_scaled, self.Y_scaled, test_size=0.2, random_state=42 # Set random_state for reproducibility
        )

            # FIX: Switched from LinearRegression() to Ridge(alpha=1.0) to combat multicollinearity
        self.model = Ridge(alpha=5.0) 
        self.model.fit(self.model_X_train, self.model_Y_train) # Train ONLY on training data

       
    def analyze_model(self):
        """
        Calculates the percentage of predictions within +/- 10 seconds (0.1667 minutes)
        of the actual pace.
        """

        vif = self._calculate_vif()
        accuracy = self.analyze_accuracy_test()
        coef_df, r_squared_train, r_squared_test = self._analyze_coefficients()
        self.generate_test_results_csv()

        return vif, accuracy, coef_df, r_squared_train, r_squared_test

    # --- NEW METHOD: Custom accuracy check ---
    def analyze_accuracy_test(self):
        """
        Calculates the percentage of predictions within +/- 10 seconds (0.1667 minutes)
        of the actual pace.
        """
        # Define the acceptable margin of error in minutes
        # 1. Predict the pace on the scaled data
        Y_predicted_scaled = self.model.predict(self.model_X_test)

        Y_predicted_scaled = Y_predicted_scaled.reshape(-1, 1)

        # 2. Inverse transform predicted and actual values to real-world pace (min/mile)
        Y_predicted = self.scaler_Y.inverse_transform(Y_predicted_scaled)
        Y_actual = self.scaler_Y.inverse_transform(self.model_Y_test)

        # 3. Calculate the absolute difference between predicted and actual pace
        pace_difference = np.abs(Y_predicted - Y_actual)

        # 4. Count how many predictions are within the 10-second margin
        accurate_count = np.sum(pace_difference <= self.MARGIN_MINUTES)

        # 5. Calculate the percentage accuracy
        accuracy_percent = round((accurate_count / len(Y_actual)) * 100, 2)
        
        return accuracy_percent

    def _calculate_vif(self):
        """Calculates and prints the Variance Inflation Factor (VIF) for each predictor."""
        
        
        # NOTE: VIF requires the data matrix to be converted to a NumPy array 
        # for efficient calculation, and we'll use the unscaled data (X)
        X_array = self.X.values
        vif_data = pd.DataFrame()
        vif_data["Feature"] = self.X.columns
        vif_data["VIF"] = [variance_inflation_factor(X_array, i) 
                            for i in range(X_array.shape[1])]
        
        # Sort by VIF score descending
        vif_data = vif_data.sort_values(by="VIF", ascending=False)
        
        return vif_data


    def _analyze_coefficients(self):
        """Prints the standardized coefficients and reports train/test scores."""
        
        coef_df = pd.DataFrame({
            'Feature': self.predictors,
            'Coefficient (Standardized)': self.model.coef_[0]
        }).sort_values(by='Coefficient (Standardized)', key=abs, ascending=False)
        

        
        # --- NEW: Calculate and report Train and Test R-squared scores ---
        try:
             r_squared_train = self.model.score(self.model_X_train, self.model_Y_train)
             r_squared_test = self.model.score(self.model_X_test, self.model_Y_test) # Score on unseen data!
             

        except Exception as e:
             print(f"\nModel Evaluation Failed: {e}")

        return coef_df, r_squared_train, r_squared_test

    def predict_pace(self, current_data: dict) -> float:
        """
        Predicts the pace for a future run based on current/forecasted data.
        """
        if self.model is None or self.scaler_X is None:
            raise Exception("Model not trained yet. Run train_model() first.")
        
        # 1. Convert input dictionary to a DataFrame in the correct order
        input_df = pd.DataFrame([current_data])[self.predictors]
        
        # 2. Scale the input data using the saved historical scales (CRITICAL!)
        input_scaled = self.scaler_X.transform(input_df)
        
        # 3. Predict the scaled Pace (Y)
        predicted_pace_scaled = self.model.predict(input_scaled)

        predicted_pace_scaled = predicted_pace_scaled.reshape(-1, 1) 
        
        # 4. Inverse transform to get the Pace in min/mile (the real world value)
        predicted_pace = self.scaler_Y.inverse_transform(predicted_pace_scaled)[0][0]
        
        return predicted_pace

    def generate_test_results_csv(self, filename="model_test_results.csv"):
        """
        Predicts pace on the test set, inverse transforms all data, and saves 
        the comparison table to a CSV file.
        """
        if self.model is None or self.model_X_test is None or self.model_Y_test is None:
            print("Model has not been trained or test data is missing.")
            return

        # 1. Predict on the test set
        Y_pred_scaled = self.model.predict(self.model_X_test)
        Y_pred_scaled = Y_pred_scaled.reshape(-1, 1)

        # 2. Inverse transform predicted, actual Y, and X features to real-world units
        Y_pred_real = self.scaler_Y.inverse_transform(Y_pred_scaled).flatten()
        Y_actual_real = self.scaler_Y.inverse_transform(self.model_Y_test).flatten()
        X_test_real = self.scaler_X.inverse_transform(self.model_X_test)

        # 3. Create DataFrame
        results_df = pd.DataFrame(X_test_real, columns=self.predictors)
        
        # Add actual and predicted pace
        results_df['Actual_Pace'] = Y_actual_real
        results_df['Predicted_Pace'] = Y_pred_real
        
        # Calculate difference and accuracy flag
        results_df['Pace_Difference_min'] = results_df['Predicted_Pace'] - results_df['Actual_Pace']
        results_df['Accurate_Within_10s'] = (results_df['Pace_Difference_min'].abs() <= self.MARGIN_MINUTES)
        
        # Round numerical columns for clean viewing
        for col in ['Actual_Pace', 'Predicted_Pace', 'Pace_Difference_min']:
            results_df[col] = results_df[col].round(2)
        
        # 4. Save to CSV
        results_df.to_csv(filename, index=False)
        print(f"\nSuccessfully generated test results in '{filename}'.")