import pandas as pd
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class Oracle:
    """
    The Oracle allows users to chat with their scraped data (DataFrame) using OpenAI.
    Attributes:
        data_df (pd.DataFrame): The data to query.
        api_key (str): OpenAI API Key.
    """
    def __init__(self, data_df, api_key):
        self.data_df = data_df
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def ask(self, question):
        """
        Answers a question based on the dataframe content.
        """
        if self.data_df is None or self.data_df.empty:
            return "❌ No data available to answer your question."
        
        if not self.api_key:
            return "❌ Please provide an OpenAI API Key."

        # Prepare context (limit to recent/relevant rows to save tokens if large)
        # For this version, we convert the head/tail or summary to text.
        # If dataset is huge, RAG would be better, but for "Excel-sized" data, this works.
        
        # Create a text representation of the data
        data_summary = self.data_df.to_csv(index=False)
        
        # Truncate if too long (rough token management)
        if len(data_summary) > 50000:
            logger.warning("Data too large for full context, truncating...")
            data_summary = data_summary[:50000] + "\n...(truncated)"

        system_prompt = (
            "You are The Oracle, an intelligent data analyst. "
            "You have access to a dataset containing web scraped information. "
            "Answer the user's question based ONLY on this data. "
            "If the answer is not in the data, say you don't know. "
            "Keep answers professional, concise, and insightful."
        )

        user_message = f"Dataset:\n{data_summary}\n\nQuestion: {question}"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Oracle Error: {e}")
            return f"❌ Oracle was silenced by an error: {e}"
