import pandas as pd
import os

def save_to_csv(data, filename='output.csv'):
    """
    Saves a list of dictionaries to a CSV file.
    """
    if not data:
        print("No data to save.")
        return

    try:
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def ensure_dir(directory):
    """
    Ensures that a directory exists.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
