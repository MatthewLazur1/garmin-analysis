import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
# from sklearn.linear_model import Ridge # Replaced
from sklearn.linear_model import LinearRegression # Added
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA # Added
from datetime import datetime, date
# from statsmodels.stats.outliers_influence import variance_inflation_factor # Removed

# --- 1. DEFINE CLASS FOR MODEL MANAGEMENT ---

class PredictivePacingModelPCA: # Renamed class slightly
    """
    Manages the training, scaling, PCA transformation, and prediction 
    of the running pace model.
    """
    def __init__(self, n_components=0.95): # Allow specifying PCA components/variance
        # The 8 original predictors (X) we will use for input
        self.original_predictors = [
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
        self.pca = None # Added PCA attribute
        self.n_components_ = None # To store the actual number of components used
        self.n_components_setting = n_components # Store user setting (e.g., 0.95 or int)
        
        # Internal storage - useful for analysis but not strictly required outside
        self._df = None
        self._X_original = None
        self._Y = None
        self._X_scaled_train = None
        self._X_scaled_test = None
        self._Y_scaled_train = None
        self._Y_scaled_test = None
        self._X_pca_train = None
        self._X_pca_test = None

        self.MARGIN_SECONDS = 15 
        self.MARGIN_MINUTES = self.MARGIN_SECONDS / 60

    def train_model(self, df: pd.DataFrame):
        """
        Trains the PCA + Linear Regression model and saves scalers and PCA transformer.
        """
        
        # --- Store the original DataFrame reference ---
        self._df = df.copy() 
        required_cols = self.original_predictors + [self.target]
        
        # --- ROBUST FIX: Handle Missing and Non-Finite Values ---
        df = df[required_cols].copy()
        df = df.dropna(subset=required_cols)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()
        
        # Separate features (X) and target (Y) from the cleaned DataFrame
        self._X_original = df[self.original_predictors]
        self._Y = df[[self.target]] # Keep as DataFrame for scaler

        # --- Standardization (Essential for PCA and regression) ---
        self.scaler_X = StandardScaler()
        self.scaler_Y = StandardScaler()
        
        X_scaled = self.scaler_X.fit_transform(self._X_original)
        # Fit scaler_Y on the entire Y dataset before splitting
        Y_scaled = self.scaler_Y.fit_transform(self._Y) 
        
        # --- Split scaled data *before* PCA ---
        self._X_scaled_train, self._X_scaled_test, self._Y_scaled_train, self._Y_scaled_test = train_test_split(
            X_scaled, Y_scaled, test_size=0.2, random_state=42 
        )

        # --- Apply PCA ---
        # If n_components is float (e.g., 0.95), it keeps components explaining that variance
        # If n_components is int, it keeps that many components
        self.pca = PCA(n_components=5) 
        
        # Fit PCA *only* on the training data
        self._X_pca_train = self.pca.fit_transform(self._X_scaled_train)
        
        # Transform the test data using the *same* fitted PCA
        self._X_pca_test = self.pca.transform(self._X_scaled_test)
        
        # Store the actual number of components selected by PCA
        self.n_components_ = self.pca.n_components_
        print(f"PCA selected {self.n_components_} components.")
        print(f"Explained variance ratio per component: {np.round(self.pca.explained_variance_ratio_, 3)}")
        print(f"Cumulative explained variance: {np.round(np.cumsum(self.pca.explained_variance_ratio_), 3)}")


        # --- Train Linear Regression Model on Principal Components ---
        self.model = LinearRegression() # Using Linear Regression on uncorrelated components
        # Train using PCA-transformed training data
        self.model.fit(self._X_pca_train, self._Y_scaled_train) 

    def analyze_model(self):
        """
        Performs analysis on the trained PCA + regression model.
        Removes VIF analysis as it's not applicable after PCA.
        """
        # vif = self._calculate_vif() # VIF is not meaningful for uncorrelated Principal Components
        accuracy = self.analyze_accuracy_test()
        coef_df, r_squared_train, r_squared_test = self._analyze_coefficients()
        self.generate_test_results_csv()

        # Return relevant results (excluding VIF)
        return accuracy, coef_df, r_squared_train, r_squared_test 


    def analyze_accuracy_test(self):
        """
        Calculates the percentage of predictions on the test set within +/- 15 seconds
        of the actual pace, using the PCA-transformed test data.
        """
        if self.model is None or self._X_pca_test is None:
             raise Exception("Model not trained or PCA transformation missing.")
             
        # 1. Predict the pace on the PCA-transformed test data
        Y_predicted_scaled = self.model.predict(self._X_pca_test)
        Y_predicted_scaled = Y_predicted_scaled.reshape(-1, 1)

        # 2. Inverse transform predicted and actual values to real-world pace (min/mile)
        Y_predicted = self.scaler_Y.inverse_transform(Y_predicted_scaled)
        # Use the stored scaled test target data
        Y_actual = self.scaler_Y.inverse_transform(self._Y_scaled_test) 

        # 3. Calculate the absolute difference between predicted and actual pace
        pace_difference = np.abs(Y_predicted - Y_actual)

        # 4. Count how many predictions are within the margin
        accurate_count = np.sum(pace_difference <= self.MARGIN_MINUTES)

        # 5. Calculate the percentage accuracy
        accuracy_percent = round((accurate_count / len(Y_actual)) * 100, 2)
        
        return accuracy_percent

    # def _calculate_vif(self): # Removed VIF calculation
    #     pass

    def _analyze_coefficients(self):
        """
        Prints the coefficients for the Principal Components and reports train/test scores.
        """
        if self.model is None:
             raise Exception("Model not trained yet.")
             
        # Create names for the principal components (PC1, PC2, ...)
        pc_names = [f'PC{i+1}' for i in range(self.n_components_)]
        
        # Coefficients now relate to the principal components
        coef_df = pd.DataFrame({
            'Principal Component': pc_names,
            'Coefficient': self.model.coef_[0] # Assuming single target variable
        }).sort_values(by='Coefficient', key=abs, ascending=False)
        
        r_squared_train = None
        r_squared_test = None
        # --- Calculate and report Train and Test R-squared scores using PCA data ---
        try:
             # Score using PCA-transformed data
             r_squared_train = self.model.score(self._X_pca_train, self._Y_scaled_train) 
             r_squared_test = self.model.score(self._X_pca_test, self._Y_scaled_test) 
             
        except Exception as e:
             print(f"\nModel Evaluation Failed: {e}")

        return coef_df, r_squared_train, r_squared_test

    def predict_pace(self, current_data: dict) -> float:
        """
        Predicts the pace for a future run based on current/forecasted data,
        applying scaling and PCA transformation first.
        """
        if self.model is None or self.scaler_X is None or self.pca is None:
            raise Exception("Model not trained yet. Run train_model() first.")
        
        # 1. Convert input dictionary to a DataFrame in the correct original feature order
        input_df = pd.DataFrame([current_data])[self.original_predictors]
        
        # 2. Scale the input data using the saved historical scales
        input_scaled = self.scaler_X.transform(input_df)
        
        # --- 3. Transform the scaled data using the fitted PCA model ---
        input_pca = self.pca.transform(input_scaled)
        
        # 4. Predict the scaled Pace (Y) using the principal components
        predicted_pace_scaled = self.model.predict(input_pca)
        predicted_pace_scaled = predicted_pace_scaled.reshape(-1, 1) 
        
        # 5. Inverse transform to get the Pace in min/mile
        predicted_pace = self.scaler_Y.inverse_transform(predicted_pace_scaled)[0][0]
        
        return predicted_pace

    def generate_test_results_csv(self, filename="model_pca_test_results.csv"): # Updated filename
        """
        Predicts pace on the test set (using PCA), inverse transforms all data 
        (original features and pace), and saves the comparison table to a CSV file.
        """
        if self.model is None or self._X_pca_test is None or self._Y_scaled_test is None:
            print("Model has not been trained or test data is missing.")
            return

        # 1. Predict on the PCA-transformed test set
        Y_pred_scaled = self.model.predict(self._X_pca_test)
        Y_pred_scaled = Y_pred_scaled.reshape(-1, 1)

        # 2. Inverse transform predicted and actual Y to real-world units
        Y_pred_real = self.scaler_Y.inverse_transform(Y_pred_scaled).flatten()
        Y_actual_real = self.scaler_Y.inverse_transform(self._Y_scaled_test).flatten()
        
        # --- Inverse transform the original scaled X test features ---
        # We need self._X_scaled_test which was created during training
        X_test_real = self.scaler_X.inverse_transform(self._X_scaled_test) 

        # 3. Create DataFrame using original feature names
        results_df = pd.DataFrame(X_test_real, columns=self.original_predictors)
        
        # Add actual and predicted pace
        results_df['Actual_Pace'] = Y_actual_real
        results_df['Predicted_Pace'] = Y_pred_real
        
        # Calculate difference and accuracy flag
        results_df['Pace_Difference_min'] = results_df['Predicted_Pace'] - results_df['Actual_Pace']
        results_df['Accurate_Within_15s'] = (results_df['Pace_Difference_min'].abs() <= self.MARGIN_MINUTES)
        
        # Round numerical columns for clean viewing
        for col in self.original_predictors + ['Actual_Pace', 'Predicted_Pace', 'Pace_Difference_min']:
             # Handle potential non-numeric columns just in case, though unlikely here
            if pd.api.types.is_numeric_dtype(results_df[col]):
                 results_df[col] = results_df[col].round(2) 
        
        # 4. Save to CSV
        results_df.to_csv(filename, index=False)
        print(f"\nSuccessfully generated PCA test results in '{filename}'.")

# --- EXAMPLE USAGE (Assuming you have your data loading function 'load_data') ---
# from your_data_loading_module import load_data 

# df = load_data() # Load your dataframe
# pca_model = PredictivePacingModelPCA(n_components=0.95) # Keep 95% variance
# pca_model.train_model(df)

# # Analyze the results
# accuracy, coef_df, r2_train, r2_test = pca_model.analyze_model()
# print(f"\nAccuracy within +/- {pca_model.MARGIN_SECONDS} seconds: {accuracy}%")
# print("\nCoefficients for Principal Components:")
# print(coef_df)
# print(f"\nTraining R-squared: {r2_train:.4f}")
# print(f"Test R-squared: {r2_test:.4f}")


# # Predict pace for a new run
# future_run_data = {
#     'distance_miles': 10.0,
#     'avg_hr': 160,
#     'temperature': 65,
#     'hrv': 55,
#     'days_since_start': 300, # Example value
#     'elevation_gain': 500,
#     'resting_heart_rate': 48,
#     'humidity': 70
# }
# predicted = pca_model.predict_pace(future_run_data)

# minutes = int(predicted)
# seconds = round((predicted - minutes) * 60)
# print(f"\nPredicted pace for new run: {minutes}:{seconds:02d} min/mile")