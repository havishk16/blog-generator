#!/usr/bin/env python3
"""
Google Sheets Manager - Manages blog topics from Google Sheets using public CSV URL
"""

import os
import pandas as pd
from datetime import datetime, date
from typing import Optional, List, Dict


class SheetsManager:
    def __init__(self):
        """Initialize Google Sheets manager with public CSV URL"""
        self.csv_url = os.getenv("GOOGLE_SHEET_CSV_URL")
        
        self.enabled = bool(self.csv_url)
        
        if not self.enabled:
            print("⚠️  Google Sheets CSV URL not found. Sheets integration is disabled.")
        else:
            print(f"✓ Google Sheets CSV URL configured")
    
    def get_topics(self) -> List[Dict]:
        """
        Fetch topics from Google Sheet via public CSV URL
        
        Returns:
            List of topic dictionaries with 'date', 'topic', and 'status' keys
        """
        if not self.enabled:
            return []
        
        try:
            # Read CSV from public URL
            df = pd.read_csv(self.csv_url)
            
            # Expected columns: Date, Topic, Status
            if df.empty:
                print("⚠️  No data found in Google Sheet")
                return []
            
            # Convert DataFrame to list of dictionaries
            topics = []
            for index, row in df.iterrows():
                # Skip rows without date or topic
                if pd.isna(row.get('Date')) or pd.isna(row.get('Topic')):
                    continue
                
                topic_dict = {
                    'date': str(row.get('Date', '')).strip(),
                    'topic': str(row.get('Topic', '')).strip(),
                    'status': str(row.get('Status', '')).strip() if not pd.isna(row.get('Status')) else '',
                    'row': index + 2  # +2 because index starts at 0 and row 1 is header
                }
                
                # Only include rows with both date and topic
                if topic_dict['date'] and topic_dict['topic']:
                    topics.append(topic_dict)
            
            print(f"✓ Fetched {len(topics)} topics from Google Sheet")
            return topics
            
        except Exception as e:
            print(f"✗ Error fetching topics from Google Sheet: {str(e)}")
            return []
    
    def get_topic_for_date(self, target_date: Optional[date] = None) -> Optional[str]:
        """
        Get the topic scheduled for a specific date
        
        Args:
            target_date: Date to get topic for (default: today)
            
        Returns:
            Topic string, or None if no topic found for the date
        """
        if target_date is None:
            target_date = date.today()
        
        topics = self.get_topics()
        
        if not topics:
            return None
        
        # Convert target date to string format for comparison
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        # Find topic matching the target date
        for topic_dict in topics:
            try:
                # Try to parse the date from the sheet
                topic_date_str = topic_dict['date']
                
                # Support multiple date formats
                for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                    try:
                        parsed_date = datetime.strptime(topic_date_str, date_format).date()
                        if parsed_date == target_date:
                            print(f"📅 Found topic for {target_date_str}: {topic_dict['topic']}")
                            return topic_dict['topic']
                        break
                    except ValueError:
                        continue
            except Exception:
                continue
        
        print(f"⚠️  No topic found for date: {target_date_str}")
        return None
    
    def get_next_available_topic(self) -> Optional[str]:
        """
        Get the next available topic (today or next future date)
        
        Returns:
            Topic string, or None if no topics available
        """
        topics = self.get_topics()
        
        if not topics:
            return None
        
        today = date.today()
        
        # First try to get today's topic
        today_topic = self.get_topic_for_date(today)
        if today_topic:
            return today_topic
        
        # If no topic for today, find the next future topic
        future_topics = []
        for topic_dict in topics:
            try:
                topic_date_str = topic_dict['date']
                for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                    try:
                        parsed_date = datetime.strptime(topic_date_str, date_format).date()
                        if parsed_date >= today:
                            future_topics.append((parsed_date, topic_dict['topic']))
                        break
                    except ValueError:
                        continue
            except Exception:
                continue
        
        if future_topics:
            # Sort by date and get the earliest
            future_topics.sort(key=lambda x: x[0])
            next_date, next_topic = future_topics[0]
            print(f"📅 Next scheduled topic for {next_date}: {next_topic}")
            return next_topic
        
        print("⚠️  No future topics found in Google Sheet")
        return None


def main():
    """CLI interface for sheets manager"""
    import sys
    
    manager = SheetsManager()
    
    if not manager.enabled:
        print("Google Sheets is not configured. Please set GOOGLE_SHEET_CSV_URL")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "today":
            topic = manager.get_topic_for_date()
            if topic:
                print(f"Today's topic: {topic}")
            else:
                print("No topic scheduled for today")
        elif command == "next":
            topic = manager.get_next_available_topic()
            if topic:
                print(f"Next topic: {topic}")
        elif command == "list":
            topics = manager.get_topics()
            print(f"\nAll topics ({len(topics)}):")
            for t in topics:
                print(f"  {t['date']}: {t['topic']} [{t['status']}]")
        else:
            print("Usage: python sheets_manager.py [today|next|list]")
            print("  today - Get today's topic")
            print("  next  - Get next available topic")
            print("  list  - List all topics")
    else:
        # Default: get next available topic
        topic = manager.get_next_available_topic()
        if topic:
            print(topic)


if __name__ == "__main__":
    main()
