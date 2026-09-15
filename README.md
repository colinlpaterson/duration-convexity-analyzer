# Duration & Convexity Analyzer

An interactive Streamlit app showing how duration and convexity approximate a
fixed-rate bond's price response to changes in yield.

## Run locally

Clone the repository, enter its directory, and install the dependencies:

```shell
git clone https://github.com/<username>/duration-convexity-analyzer.git
cd duration-convexity-analyzer
python -m pip install -r requirements.txt
```

Start the app:

```shell
python -m streamlit run app.py
```

Streamlit will display the local URL in the terminal, typically
`http://localhost:8501`. Press `Ctrl+C` to stop the app.

## Run the tests

```shell
python -m pytest
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Sign in to Streamlit Community Cloud and create a new app.
3. Select the repository and branch.
4. Set the entry-point file to `app.py`.
5. Deploy the app.

The sidebar controls the bond terms, current yield, and chart range. Use the
scenario slider beneath the chart to compare both approximations with an exact
repricing.
