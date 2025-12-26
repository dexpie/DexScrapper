import pandas as pd
import os
import json
import logging

logger = logging.getLogger(__name__)

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
        logger.info(f"Data successfully saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving CSV: {e}")

def save_to_excel(data, filename='output.xlsx'):
    """
    Saves a list of dictionaries to an Excel file.
    """
    if not data:
        print("No data to save.")
        return

    try:
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        logger.info(f"Data successfully saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving Excel: {e}")

def save_to_json(data, filename='output.json'):
    """
    Saves a list of dictionaries to a JSON file.
    """
    if not data:
        print("No data to save.")
        return

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Data successfully saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving JSON: {e}")

def save_to_markdown(title, url, content, folder="output/markdown"):
    """
    Saves content as a Markdown file.
    """
    try:
        ensure_dir(folder)
        # Sanitize filename
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]
        if not safe_title:
             safe_title = "untitled"
        
        filename = f"{safe_title}.md"
        filepath = os.path.join(folder, filename)
        
        md_content = f"# {title}\n\n**Source:** {url}\n\n---\n\n{content}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return filepath
    except Exception as e:
        logger.error(f"Error saving Markdown: {e}")
        return None

def ensure_dir(directory):
    """
    Ensures that a directory exists.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
