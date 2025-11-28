#!/usr/bin/env python3
"""
Topic Manager - Handles topic rotation for daily blog generation
"""

import os
from typing import Optional


class TopicManager:
    def __init__(self, topics_file: str = "topics.txt", index_file: str = ".last_topic_index"):
        """
        Initialize the Topic Manager
        
        Args:
            topics_file: Path to file containing topics (one per line)
            index_file: Path to file storing the last used topic index
        """
        self.topics_file = topics_file
        self.index_file = index_file
        self.topics = self._load_topics()
    
    def _load_topics(self) -> list:
        """Load topics from the topics file"""
        if not os.path.exists(self.topics_file):
            print(f"⚠️  Topics file '{self.topics_file}' not found.")
            return []
        
        topics = []
        with open(self.topics_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    topics.append(line)
        
        return topics
    
    def _get_last_index(self) -> int:
        """Get the last used topic index"""
        if not os.path.exists(self.index_file):
            return -1
        
        try:
            with open(self.index_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return -1
    
    def _save_index(self, index: int):
        """Save the current topic index"""
        with open(self.index_file, 'w') as f:
            f.write(str(index))
    
    def get_next_topic(self) -> Optional[str]:
        """
        Get the next topic in rotation
        First tries Google Sheets (if configured), then falls back to local file
        
        Returns:
            Next topic string, or None if no topics available
        """
        # Try Google Sheets first
        try:
            from sheets_manager import SheetsManager
            sheets = SheetsManager()
            
            if sheets.enabled:
                topic = sheets.get_next_available_topic()
                if topic:
                    return topic
                else:
                    print("⚠️  No topics found in Google Sheets, falling back to local file...")
        except ImportError:
            print("⚠️  Google Sheets module not available, using local file...")
        except Exception as e:
            print(f"⚠️  Error accessing Google Sheets: {str(e)}, falling back to local file...")
        
        # Fall back to local file rotation
        if not self.topics:
            print("⚠️  No topics available in topics file.")
            return None
        
        # Get the last used index and increment
        last_index = self._get_last_index()
        next_index = (last_index + 1) % len(self.topics)
        
        # Save the new index
        self._save_index(next_index)
        
        topic = self.topics[next_index]
        print(f"📝 Selected topic {next_index + 1}/{len(self.topics)}: {topic}")
        
        return topic
    
    def get_current_topic(self) -> Optional[str]:
        """
        Get the current topic without advancing the index
        
        Returns:
            Current topic string, or None if no topics available
        """
        if not self.topics:
            return None
        
        last_index = self._get_last_index()
        if last_index == -1:
            return self.topics[0]
        
        return self.topics[last_index % len(self.topics)]
    
    def reset(self):
        """Reset the topic rotation to the beginning"""
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        print("✓ Topic rotation reset to beginning")


def main():
    """CLI interface for topic manager"""
    import sys
    
    manager = TopicManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "next":
            topic = manager.get_next_topic()
            if topic:
                print(topic)
        elif command == "current":
            topic = manager.get_current_topic()
            if topic:
                print(f"Current topic: {topic}")
        elif command == "reset":
            manager.reset()
        else:
            print("Usage: python topic_manager.py [next|current|reset]")
            print("  next    - Get next topic and advance rotation")
            print("  current - Get current topic without advancing")
            print("  reset   - Reset rotation to beginning")
    else:
        # Default: get next topic
        topic = manager.get_next_topic()
        if topic:
            print(topic)


if __name__ == "__main__":
    main()
