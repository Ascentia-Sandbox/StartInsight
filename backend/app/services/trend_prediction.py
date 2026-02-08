"""Trend prediction service using Prophet for time-series forecasting.

This service implements AI-powered trend prediction for Google Trends data,
providing 7-day ahead forecasts with confidence intervals.

Phase 9.1: AI-Powered Trend Prediction
- Train Prophet model on historical trend data (90+ days)
- Generate 7-day ahead predictions
- Include upper/lower confidence intervals
- Cache predictions for 24 hours
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
from prophet import Prophet
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TrendPredictionService:
    """
    Service for generating time-series predictions using Facebook Prophet.

    Prophet is a production-ready forecasting library that:
    - Handles missing data automatically
    - Detects seasonality (daily, weekly, yearly)
    - Includes trend changepoints
    - Provides confidence intervals
    - Requires minimal hyperparameter tuning
    """

    def __init__(self):
        """Initialize the trend prediction service."""
        self.model = None
        self.logger = logger

    async def train_and_predict(
        self,
        trend_data: dict[str, Any],
        periods: int = 7,
    ) -> dict[str, Any]:
        """
        Train Prophet model on historical trend data and generate predictions.

        Args:
            trend_data: Dictionary with 'dates' and 'values' arrays
            periods: Number of days to forecast ahead (default: 7)

        Returns:
            Dictionary with prediction data:
            {
                "dates": ["2026-01-29", "2026-01-30", ...],
                "values": [85, 87, 90, ...],
                "confidence_intervals": {
                    "lower": [80, 82, 85, ...],
                    "upper": [90, 92, 95, ...]
                },
                "model_accuracy": {
                    "mape": 0.15,  # Mean Absolute Percentage Error
                    "rmse": 5.2    # Root Mean Squared Error
                }
            }

        Raises:
            ValueError: If trend_data has insufficient historical data (<7 days)
        """
        try:
            # Extract dates and values
            dates = trend_data.get("dates", [])
            values = trend_data.get("values", [])

            if len(dates) < 7:
                raise ValueError(
                    f"Insufficient data for prediction: {len(dates)} days "
                    "(minimum 7 required)"
                )

            # Prepare data for Prophet (requires 'ds' and 'y' columns)
            df = pd.DataFrame({
                "ds": pd.to_datetime(dates),
                "y": values
            })

            # Initialize Prophet model
            # interval_width=0.80 provides 80% confidence intervals
            # daily_seasonality=False (not enough intra-day data)
            # weekly_seasonality='auto' (detect if present)
            # yearly_seasonality=False (not enough data)
            self.model = Prophet(
                interval_width=0.80,
                daily_seasonality=False,
                weekly_seasonality='auto',
                yearly_seasonality=False,
                changepoint_prior_scale=0.05,  # Flexibility of trend changes
            )

            # Train the model
            self.logger.info(
                f"Training Prophet model on {len(df)} data points "
                f"(from {df['ds'].min()} to {df['ds'].max()})"
            )
            self.model.fit(df)

            # Generate future dataframe for next N days
            future = self.model.make_future_dataframe(periods=periods)

            # Make predictions
            forecast = self.model.predict(future)

            # Extract prediction values (last N rows)
            prediction_rows = forecast.tail(periods)

            # Format predictions
            predictions = {
                "dates": prediction_rows["ds"].dt.strftime("%Y-%m-%d").tolist(),
                "values": prediction_rows["yhat"].round(0).astype(int).tolist(),
                "confidence_intervals": {
                    "lower": prediction_rows["yhat_lower"].round(0).astype(int).tolist(),
                    "upper": prediction_rows["yhat_upper"].round(0).astype(int).tolist(),
                },
                "model_accuracy": self._calculate_accuracy(df, forecast),
                "metadata": {
                    "forecast_date": datetime.now(UTC).isoformat(),
                    "training_data_points": len(df),
                    "prediction_horizon": periods,
                }
            }

            self.logger.info(
                f"Generated {periods}-day prediction with "
                f"MAPE={predictions['model_accuracy']['mape']:.2%}"
            )

            return predictions

        except Exception as e:
            self.logger.error(f"Prediction failed: {type(e).__name__} - {e}")
            raise

    def _calculate_accuracy(
        self,
        historical_df: pd.DataFrame,
        forecast_df: pd.DataFrame
    ) -> dict[str, float]:
        """
        Calculate model accuracy metrics on historical data.

        Args:
            historical_df: Original training data
            forecast_df: Full forecast dataframe (includes historical fit)

        Returns:
            Dictionary with accuracy metrics (MAPE, RMSE)
        """
        try:
            # Match historical dates with forecast
            merged = historical_df.merge(forecast_df[['ds', 'yhat']], on='ds')

            # Calculate MAPE (Mean Absolute Percentage Error)
            actual = merged['y']
            predicted = merged['yhat']

            # Avoid division by zero
            non_zero = actual != 0
            mape = (
                ((actual[non_zero] - predicted[non_zero]).abs() / actual[non_zero].abs())
                .mean()
            )

            # Calculate RMSE (Root Mean Squared Error)
            rmse = ((actual - predicted) ** 2).mean() ** 0.5

            return {
                "mape": float(mape),
                "rmse": float(rmse),
            }

        except Exception as e:
            self.logger.warning(f"Accuracy calculation failed: {e}")
            return {"mape": 0.0, "rmse": 0.0}


async def generate_trend_predictions(
    trend_data: dict[str, Any],
    periods: int = 7,
) -> dict[str, Any]:
    """
    Standalone function to generate trend predictions.

    This is the main entry point for the trend prediction service.

    Args:
        trend_data: Historical trend data with 'dates' and 'values'
        periods: Number of days to forecast (default: 7)

    Returns:
        Prediction dictionary with dates, values, and confidence intervals

    Example:
        >>> trend_data = {
        ...     "dates": ["2026-01-01", "2026-01-02", ...],
        ...     "values": [75, 78, 80, 82, ...]
        ... }
        >>> predictions = await generate_trend_predictions(trend_data)
        >>> print(predictions["dates"])  # ["2026-01-29", "2026-01-30", ...]
        >>> print(predictions["values"])  # [85, 87, 90, ...]
    """
    service = TrendPredictionService()
    return await service.train_and_predict(trend_data, periods)
