
# Trading App

This is a trading app that includes features for backtesting, strategy evaluation, and more. Follow the instructions below to set up the project.

## Prerequisites

Before running the app, ensure you have the following installed:

- [Poetry](https://python-poetry.org/docs/)
- Python 3.8+ (recommended)

## Installation Instructions

### 1. Install Poetry

To install Poetry, run the following command:

**For macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**For Windows:**
```bash
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicP) | python -
```

For further installation instructions, check the [official Poetry documentation](https://python-poetry.org/docs/#installation).

### 2. Activate Poetry Virtual Environment and Install Dependencies

Once Poetry is installed, navigate to the root directory of your `trading_app` project and run the following command to create and activate the virtual environment:

```bash
poetry shell
```

Then, install all the required dependencies:

```bash
poetry install
```

### 3. Add `.env` File in `/backtesting` Folder

Create a `.env` file in the `/backtesting` folder with the following variables:

```bash
POLYGON_API_KEY=your_polygon_api_key_here
EXECUTED_TRADES_FILE_PATH=your_trades_file_path_here
LOGS_FILE_PATH=your_logs_file_path_here
```

Replace the values with your actual keys and file paths.

### 4. Run the App

Now, you can run the main script (`main.py`). From the root of the project, run:

```bash
poetry run python main.py
```

This will execute the main script and start the trading app.

## Additional Notes

- Make sure to securely handle your `.env` file and keep your API keys private.
- Check the logs for any errors or output related to the backtesting process.

For more information on using the app, refer to the documentation in the project directory.
