import pandas as pd
import feature_store
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import loguru
import matplotlib.pyplot as plt
import seaborn as sns

# Set pandas display option to show all rows
pd.set_option('display.max_rows', None)

# Fetch data
fs = feature_store.Connection()
data = fs.fetch_training_data()

# Drop unnecessary columns (based on domain knowledge)
data = data.drop(columns=['ticker', 'company_cik', 'key', 'timestamp', 'date', 'coding', 'price'])

# Drop rows with missing values
data = data.dropna()

# Define features (X) and target (y)
X = data.drop(columns=['pct_change'])
y = data['pct_change']

# Feature scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Feature selection: using Random Forest to check feature importance
model = RandomForestRegressor()
model.fit(X_scaled, y)
importances = pd.Series(model.feature_importances_, index=X.columns)
loguru.logger.info(f"Feature Importances: {importances.sort_values(ascending=False)}")

# Train a linear regression model with the selected features
X_selected = X[importances.nlargest(1).index]  # Use top 5 important features
X_train, X_test, y_train, y_test = train_test_split(X_selected, y, test_size=0.2, random_state=42)

regressor = LinearRegression()
regressor.fit(X_train, y_train)

# Make predictions
y_pred = regressor.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

loguru.logger.info(f"Mean Squared Error: {mse:.4f}")
loguru.logger.info(f"R² Score: {r2:.4f}")

# Merging predictions with actual pct_change for comparison
merged_df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})

# Debug: Log all rows of the merged DataFrame where predictions are negative
loguru.logger.info(f"Merged DataFrame (Predicted Negative Returns):\n{merged_df[merged_df['Predicted'] < -0.2].head(150)}")

# Plotting the correlation for predictions < 0
negative_predictions = merged_df[merged_df['Predicted'] < -0.1]
plt.figure(figsize=(10, 6))
sns.scatterplot(x=negative_predictions['Actual'], y=negative_predictions['Predicted'])
plt.title('Correlation of Actual vs Predicted for Negative Returns')
plt.xlabel('Actual pct_change')
plt.ylabel('Predicted pct_change')

# Save the plot to a file (use a complete file path with the .png extension)
plt.savefig('/app/src/plot.png') # Specify the full path, e.g., '/home/user/plot.png'
plt.close()  # Close the plot to free up memory

breakpoint()