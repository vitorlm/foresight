# ForeSight

This project is a Monte Carlo-based tool for enhancing the predictability of project cycles, leveraging Jira data. It helps in providing probabilistic estimates (P50, P85, P95) for issues based on historical and planned data.

## Features

- Fetches historical and planned data from Jira via its API.
- Performs Monte Carlo simulations to predict completion dates of epics.
- Calculates key metrics like mean duration, P50, and P90 to aid project planning.

## Project Structure

```
project-root/
├── src/
│   ├── config.py             # Loads environment variables (Jira API credentials)
│   ├── jira_api.py           # Functions to interact with Jira API
│   ├── utils.py              # Utility functions for loading and saving data
│   ├── main.py               # Main script to execute the application
├── .env                      # Environment variables file (Jira URL, credentials)
├── requirements.txt          # Project dependencies
├── README.md                 # Project documentation
└── tests/                    # Unit tests for the different modules
```

## Prerequisites

- Python 3.8 or higher
- Jira API access
- Git (for version control)

## Installation

1. **Clone the repository**:

   ```sh
   git clone https://github.com/yourusername/monte-carlo-project-planner.git
   cd monte-carlo-project-planner
   ```

2. **Set up a virtual environment** (recommended):

   ```sh
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scriptsctivate`
   ```

3. **Install the dependencies**:

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up your environment variables**:

   Create a `.env` file in the root directory with the following variables:

   ```plaintext
   JIRA_URL=https://your-jira-url.atlassian.net
   EMAIL=your-email@example.com
   API_TOKEN=your-api-token
   ```

## Running the Project

- To run the main script:

  ```sh
  python -m src.main
  ```

  This command will fetch epics from Jira, calculate their completion estimates, and provide output with key metrics.

## Usage

- **Monte Carlo Simulation**: The project uses historical cycle times to run simulations and predict when planned epics will be completed.
- **Jira Integration**: Fetches historical and planned data for epics from Jira. The `jira_api.py` handles all API interactions.

## Configuration

- **API Credentials**: The `.env` file is used to store Jira credentials. Make sure to add the `.env` file to `.gitignore` to prevent sensitive information from being shared.

## Testing

- All test cases are located in the `tests/` directory. You can run the tests using `pytest`:

  ```sh
  pytest tests/
  ```

## Project Details

This project is developed to help in forecasting epic delivery using statistical models, specifically the Monte Carlo simulation method. It leverages Jira's historical data for improved estimates.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch-name`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch-name`).
6. Open a pull request.

## License

This project is licensed under the MIT License.

## Acknowledgements

- **Python-DoTenV** for managing environment variables.
- **Workalendar** for calculating business days, excluding weekends and holidays.
- **Numpy** for numerical operations.
