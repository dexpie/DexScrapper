import pandas as pd
import asyncio
import logging
from src.cerebro import CerebroAgent

logger = logging.getLogger(__name__)

class Alchemist:
    """
    Turns base data into gold (Enrichment Agent).
    Uses Cerebro to research missing fields row-by-row.
    """
    def __init__(self, api_key):
        self.cerebro = CerebroAgent(api_key)

    async def transmute(self, df: pd.DataFrame, target_column: str, prompt_template: str, update_callback=None):
        """
        Iterates over the DataFrame, uses the value in `target_column` to fill the prompt,
        performs research, and returns a new DataFrame with an 'enriched_data' column.
        """
        enriched_results = []
        total = len(df)
        
        for index, row in df.iterrows():
            try:
                target_value = row.get(target_column)
                if not target_value:
                    enriched_results.append("N/A (Missing Target)")
                    continue
                
                # Construct query
                query = prompt_template.format(target=target_value)
                if update_callback: 
                    update_callback(f"⚗️ Transmuting ({index+1}/{total}): {target_value}...")
                
                # Perform Research (using Cerebro's research_topic but simplified)
                # We essentially want a quick answer, not a full report.
                # Let's use a specialized method or just parse the report.
                # For V13, we'll use Cerebro's existing capability which returns a Markdown report.
                # Ideally, we'd want just the specific data point, but a report is "richer".
                
                report = await self.cerebro.research_topic(query, lambda x: None) # Suppress internal logs
                
                # Store the result
                enriched_results.append(report[:500] + "...") # Store summary to avoid DB bloat? Or full?
                # Let's store full for now, users can clean later.
                
                # Small delay to respect rate limits
                await asyncio.sleep(1) 
                
            except Exception as e:
                logger.error(f"Alchemy failed for row {index}: {e}")
                enriched_results.append(f"Error: {e}")

        df['enriched_data'] = enriched_results
        return df
