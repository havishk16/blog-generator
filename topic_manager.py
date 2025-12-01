#!/usr/bin/env python3
"""
Topic Manager - Handles topic rotation and date-based scheduling from local file
"""

import os
from datetime import datetime, date
from typing import Optional, List, Dict


class TopicManager:
    def __init__(self, topics_file: str = "topics_schedule.txt"):
        """
        Initialize the Topic Manager
        
        Args:
            topics_file: Path to file containing topics with dates (format: YYYY-MM-DD|Topic)
        """
        self.topics_file = topics_file
        self.topics = self._load_topics()
    
    def _load_topics(self) -> List[Dict]:
        """Load topics with dates from the topics file"""
        if not os.path.exists(self.topics_file):
            print(f"⚠️  Topics file '{self.topics_file}' not found.")
            return []
        
        topics = []
        with open(self.topics_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse date|topic format
                if '|' in line:
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        date_str, topic = parts
                        topics.append({
                            'date': date_str.strip(),
                            'topic': topic.strip(),
                            'line': line_num
                        })
        
        return topics
    
    def get_topic_for_date(self, target_date: Optional[date] = None) -> Optional[str]:
        """
        Get the topic scheduled for a specific date
        
        Args:
            target_date: Date to get topic for (default: today in UTC)
            
        Returns:
            Topic string, or None if no topic found for the date
        """
        if target_date is None:
            target_date = datetime.utcnow().date()  # Use UTC for GitHub Actions compatibility
        
        if not self.topics:
            return None
        
        # Convert target date to string format for comparison
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        # Find topic matching the target date
        for topic_dict in self.topics:
            try:
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
        Uses UTC date for GitHub Actions compatibility
        
        Returns:
            Topic string, or None if no topics available
        """
        if not self.topics:
            print("⚠️  No topics available in topics file.")
            return None
        
        today = datetime.utcnow().date()  # Use UTC for GitHub Actions
        
        # First try to get today's topic
        today_topic = self.get_topic_for_date(today)
        if today_topic:
            return today_topic
        
        # If no topic for today, find the next future topic
        future_topics = []
        for topic_dict in self.topics:
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
        
        print("⚠️  No future topics found")
        return None
    
    def get_all_topics(self) -> List[Dict]:
        """Get all topics with their dates"""
        return self.topics
    
    def reset(self):
        """Reload topics from file"""
        self.topics = self._load_topics()
        print("✓ Topics reloaded from file")


def main():
    """CLI interface for topic manager"""
    import sys
    
    manager = TopicManager()
    
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
            topics = manager.get_all_topics()
            print(f"\nAll topics ({len(topics)}):")
            for t in topics:
                print(f"  {t['date']}: {t['topic']}")
        else:
            print("Usage: python topic_manager.py [today|next|list]")
            print("  today - Get today's topic (UTC)")
            print("  next  - Get next available topic")
            print("  list  - List all topics")
    else:
        # Default: get next available topic
        topic = manager.get_next_available_topic()
        if topic:
            print(topic)


if __name__ == "__main__":
    main()
