# Spot Prices Data Collection System

## Project Overview

The Spot Prices Data Collection System is designed to fetch, store, and analyze electricity spot prices from Awattar and SmartEnergy APIs. This system aims to provide a comprehensive view of electricity prices, enabling users to make informed decisions based on real-time data.

## Core Requirements

### Data Collection

- **Fetch Spot Prices:**
  - Retrieve spot prices from the Awattar API: [Awattar API](https://api.awattar.at/v1/marketdata)
  - Retrieve spot prices from the SmartEnergy API: [SmartEnergy API](https://apis.smartenergy.at/market/v1/price)
- **Handle API Failures:**
  - Implement graceful handling of API failures with fallback values.
- **Default Timespan:**
  - Default timespan for data collection: Today 00:00 to Tomorrow 24:00.

### Data Storage

- **Store Spot Prices:**
  - Store spot prices with timestamps, price, unit, and source.
- **Calculate Daily Statistics:**
  - Calculate and store daily statistics including minimum, maximum, and average prices.
- **Track Price Times:**
  - Track the times of minimum and maximum prices per day.
- **Support Multiple Sources:**
  - Support multiple price sources in parallel.

### Visualization

- **ASCII Chart Visualization:**
  - Provide ASCII chart visualization of price trends.
- **Mark Min/Max Prices:**
  - Mark minimum and maximum prices with percentages.
- **Highlight Negative Prices:**
  - Highlight negative prices in red.
- **Custom Chart Height:**
  - Support custom chart height for better visualization.

This system ensures that users have access to accurate and up-to-date electricity spot prices, enabling them to optimize their energy usage and costs effectively.
