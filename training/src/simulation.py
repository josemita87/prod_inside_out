"""Trading simulation and prediction plotting utilities."""

import logging

import matplotlib.pyplot as plt
import seaborn as sns
from config import config

logger = logging.getLogger(__name__)


def plot_predictions(y_test, y_pred_reg, financial_results, capital_invested):
    """Plot actual vs predicted negative returns and financial results.

    Args:
        y_test: Actual negative returns.
        y_pred_reg: Predicted negative returns.
        financial_results: Final capital resulting from the simulation.
        capital_invested: Total capital invested during the simulation.
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=y_test, y=y_pred_reg)
    plt.title('Actual vs Predicted Negative Returns (Filtered by Classifier)')
    plt.xlabel('Actual Negative Returns')
    plt.ylabel('Predicted Negative Returns')
    plt.axhline(0, color='red', linestyle='--', linewidth=1)  # Mark the zero line
    plt.axvline(0, color='red', linestyle='--', linewidth=1)
    plt.grid(True)

    # Financial result annotation
    plt.figtext(0.99, 0.01, f'Final Financial Result: ${financial_results:.2f}', ha='right', fontsize=12, color='green')
    plt.figtext(0.99, 0.10, f'Capital Invested: ${capital_invested:.2f}', ha='right', fontsize=12, color='green')

    # Save plot
    plt.savefig(config.plot_path, dpi=300)
    plt.close()
    logger.info(f'Plot saved as {config.plot_path}')


def run_simulation(real_returns, y_pred_negative, investment=100, threshold=-0.3):
    """Run a simulation based on the model's predictions.

    Args:
        real_returns: Actual percentage-change returns aligned with the
            predictions.
        y_pred_negative: Predicted negative returns to evaluate.
        investment: Capital allocated to each short position. Defaults to 100.
        threshold: Predicted-return cutoff at or below which a position is
            taken. Defaults to -0.3.

    Returns:
        A tuple of the total capital invested, the accumulated gains, the
        actual returns, and the predicted negative returns.
    """
    # Simulate the investment
    gains = 0
    capital_invested = investment
    # For each time the model predicted a negative return
    for i, predicted_change in enumerate(y_pred_negative):
        if predicted_change <= threshold:
            gains += (-investment) * real_returns.iloc[i]  # Use the actual pct_change (not predicted) to update capital
            capital_invested += investment  # Update capital invested

    return capital_invested, gains, real_returns, y_pred_negative
