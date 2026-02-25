"""
Interview and Podcast Search for LeadPrep AI.

This module searches for recent interviews, podcasts, and media appearances
of company leaders using YouTube API and other sources.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class InterviewSearcher:
    """Search for interviews and podcasts featuring company leaders."""
    
    def __init__(self):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

        if not self.youtube_api_key:
            print("⚠️  YOUTUBE_API_KEY not found in environment variables")
            print("   Please set your YouTube API key in a .env file")

        if not self.anthropic_api_key:
            print("⚠️  ANTHROPIC_API_KEY not found in environment variables")
            print("   Please set your Anthropic API key in a .env file")
    
    def generate_search_queries(self, leader_name: str, company_name: str) -> List[str]:
        """
        Use a single, simple search query for the leader interview.
        Args:
            leader_name (str): Name of the leader
            company_name (str): Name of the company
        Returns:
            List[str]: List of search queries
        """
        return [f'{leader_name} interview']
    
    def search_youtube(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search YouTube for videos matching the query.
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: List of video information
        """
        if not self.youtube_api_key:
            print("❌ YouTube API key not available")
            return []
        
        try:
            # Calculate date 6 months ago
            six_months_ago = datetime.now() - timedelta(days=180)
            published_after = six_months_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # First, search for videos
            search_url = "https://www.googleapis.com/youtube/v3/search"
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'order': 'relevance',  # Changed to relevance for better quality
                'publishedAfter': published_after,
                'relevanceLanguage': 'en',
                'key': self.youtube_api_key
            }
            
            search_response = requests.get(search_url, params=search_params, timeout=30)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]
                
                if not video_ids:
                    return []
                
                # Get detailed video statistics
                videos_url = "https://www.googleapis.com/youtube/v3/videos"
                videos_params = {
                    'part': 'snippet,statistics,contentDetails',
                    'id': ','.join(video_ids),
                    'key': self.youtube_api_key
                }
                
                videos_response = requests.get(videos_url, params=videos_params, timeout=30)
                
                if videos_response.status_code == 200:
                    videos_data = videos_response.json()
                    videos = []
                    
                    for item in videos_data.get('items', []):
                        snippet = item['snippet']
                        statistics = item.get('statistics', {})
                        content_details = item.get('contentDetails', {})
                        
                        # Parse duration (ISO 8601 format)
                        duration_str = content_details.get('duration', 'PT0S')
                        duration_seconds = self.parse_duration(duration_str)
                        
                        video_info = {
                            'video_id': item['id'],
                            'title': snippet['title'],
                            'description': snippet['description'],
                            'channel_title': snippet['channelTitle'],
                            'channel_id': snippet['channelId'],
                            'published_at': snippet['publishedAt'],
                            'thumbnail': snippet['thumbnails']['medium']['url'],
                            'url': f"https://www.youtube.com/watch?v={item['id']}",
                            'query': query,
                            'view_count': int(statistics.get('viewCount', 0)),
                            'like_count': int(statistics.get('likeCount', 0)),
                            'comment_count': int(statistics.get('commentCount', 0)),
                            'duration_seconds': duration_seconds,
                            'duration_formatted': self.format_duration(duration_seconds)
                        }
                        videos.append(video_info)
                    
                    return videos
                else:
                    print(f"❌ YouTube videos API error: {videos_response.status_code}")
                    return []
            else:
                print(f"❌ YouTube search API error: {search_response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching YouTube for '{query}': {e}")
            return []
    
    def parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration string to seconds.
        
        Args:
            duration_str (str): Duration in ISO 8601 format (e.g., "PT1H2M30S")
            
        Returns:
            int: Duration in seconds
        """
        import re
        
        # Parse PT1H2M30S format
        hours = re.search(r'(\d+)H', duration_str)
        minutes = re.search(r'(\d+)M', duration_str)
        seconds = re.search(r'(\d+)S', duration_str)
        
        total_seconds = 0
        if hours:
            total_seconds += int(hours.group(1)) * 3600
        if minutes:
            total_seconds += int(minutes.group(1)) * 60
        if seconds:
            total_seconds += int(seconds.group(1))
            
        return total_seconds
    
    def format_duration(self, seconds: int) -> str:
        """
        Format seconds to human-readable duration.
        
        Args:
            seconds (int): Duration in seconds
            
        Returns:
            str: Formatted duration (e.g., "1:30:45")
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def search_leader_interviews(self, leader_name: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Search for interviews and media appearances of a leader.
        
        Args:
            leader_name (str): Name of the leader
            company_name (str): Name of the company
            
        Returns:
            List[Dict[str, Any]]: List of interview/podcast information
        """
        print(f"🔍 Searching for interviews with {leader_name} from {company_name}...")
        
        # Generate search queries
        queries = self.generate_search_queries(leader_name, company_name)
        print(f"📝 Generated {len(queries)} search queries")
        
        all_results = []
        
        # Search YouTube for each query
        for query in queries:
            print(f"  Searching: '{query}'")
            videos = self.search_youtube(query, max_results=8)  # Increased to get more candidates
            all_results.extend(videos)
        
        # Remove duplicates based on video_id
        unique_results = {}
        for result in all_results:
            video_id = result['video_id']
            if video_id not in unique_results:
                unique_results[video_id] = result
        
        # Convert back to list
        unique_videos = list(unique_results.values())
        
        # Filter and rank videos
        print(f"📊 Scoring and filtering {len(unique_videos)} unique videos...")
        filtered_videos = self.filter_and_rank_videos(unique_videos, leader_name, company_name)
        
        # Sort by date within score groups
        filtered_videos.sort(key=lambda x: (x['relevance_score'], x['published_at']), reverse=True)
        
        print(f"✅ Found {len(filtered_videos)} high-quality videos for {leader_name}")
        
        # Show top results with scores
        for i, video in enumerate(filtered_videos[:5]):
            print(f"  {i+1}. [{video['relevance_score']:.0f}] {video['title']}")
            print(f"     Channel: {video['channel_title']}")
        
        return filtered_videos[:15]  # Return top 15 results
    
    def search_multiple_leaders(self, leaders: List[Dict[str, str]], company_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for interviews for multiple leaders.
        
        Args:
            leaders (List[Dict[str, str]]): List of leaders with name and title
            company_name (str): Name of the company
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary mapping leader names to their interviews
        """
        results = {}
        
        for leader in leaders:
            leader_name = leader['name']
            interviews = self.search_leader_interviews(leader_name, company_name)
            results[leader_name] = interviews
        
        return results
    
    def score_video_relevance(self, video_info: Dict[str, Any], leader_name: str, company_name: str) -> float:
        """
        Score a video based on its strategic value and likelihood of containing executive insights.
        
        Args:
            video_info (Dict[str, Any]): Video information from YouTube API
            leader_name (str): Name of the leader
            company_name (str): Name of the company
            
        Returns:
            float: Strategic relevance score (0-100)
        """
        title = video_info['title'].lower()
        description = video_info['description'].lower()
        channel_title = video_info['channel_title'].lower()
        duration_seconds = video_info.get('duration_seconds', 0)
        view_count = video_info.get('view_count', 0)
        
        # Filter: Only consider videos at least 10 minutes long
        if duration_seconds < 600:
            return 0
        
        score = 0.0
        
        # Premium business media channels (highest strategic value)
        premium_channels = [
            'cnbc', 'bloomberg', 'wsj', 'wall street journal', 'reuters', 
            'financial times', 'forbes', 'fortune', 'axios', 'recode'
        ]
        
        # Strategic business channels
        strategic_channels = [
            'ted', 'tedx', 'sxsw', 'code conference', 'all things d',
            'goldman sachs', 'jpmorgan', 'morgan stanley', 'goldman sachs talks'
        ]
        
        # Official company channels
        official_channels = [
            company_name.lower(), f'{company_name.lower()} official',
            f'{company_name.lower()} investor relations', f'{company_name.lower()} events'
        ]
        
        # Channel quality scoring
        if any(channel in channel_title for channel in premium_channels):
            score += 35  # Highest value for premium business media
        elif any(channel in channel_title for channel in strategic_channels):
            score += 30  # High value for strategic business events
        elif any(channel in channel_title for channel in official_channels):
            score += 25  # Good value for official company content
        elif 'earnings' in channel_title or 'investor' in channel_title:
            score += 20
        elif 'conference' in channel_title or 'summit' in channel_title:
            score += 18
        
        # CRITICAL: Check if this is actually about the right person
        if company_name.lower() not in title and company_name.lower() not in description:
            score -= 50  # Heavy penalty if company not mentioned
        
        # Interview indicators
        interview_keywords = [
            'interview with', 'exclusive interview', 'fireside chat', 'q&a', 'in conversation with',
            'panel discussion', 'moderated by', 'talks to', 'answers questions', 'one-on-one',
            'sits down with', 'conversation with', 'ceo interview', 'leadership interview', 'executive interview'
        ]
        # Strong boost for interview indicators
        for keyword in interview_keywords:
            if keyword in title or keyword in description:
                score += 30
        
        # Penalize indirect mentions (about, discusses, reacts to, etc.)
        indirect_keywords = [
            f'about {leader_name.lower()}', f'discusses {leader_name.lower()}', f'reacts to {leader_name.lower()}',
            f'news on {leader_name.lower()}', f'latest on {leader_name.lower()}'
        ]
        for keyword in indirect_keywords:
            if keyword in title or keyword in description:
                score -= 30
        
        # Strategic content indicators in title
        strategic_keywords = [
            'strategy', 'vision', 'leadership', 'business', 'future', 'innovation',
            'earnings', 'investor', 'conference', 'keynote', 'summit', 'panel',
            'interview', 'discussion', 'presentation', 'announcement'
        ]
        for keyword in strategic_keywords:
            if keyword in title:
                score += 8
        
        # Exact name match (critical for relevance)
        if f'"{leader_name.lower()}"' in title or leader_name.lower() in title:
            score += 25
        
        # Company name in title
        if company_name.lower() in title:
            score += 10
        
        # Duration scoring (longer = more substantial discussion)
        if duration_seconds > 1800:  # 30+ minutes
            score += 15
        elif duration_seconds > 900:  # 15+ minutes
            score += 10
        elif duration_seconds > 600:  # 10+ minutes
            score += 5
        
        # View count scoring (engagement indicator)
        if view_count > 100000:  # 100k+ views
            score += 8
        elif view_count > 10000:  # 10k+ views
            score += 5
        elif view_count > 1000:  # 1k+ views
            score += 2
        
        # Heavy penalties for clearly wrong content
        heavy_negative_keywords = [
            'quit', 'fired', 'resigns', 'leaves', 'last day', 'goodbye',
            'reaction', 'summary', 'recap', 'analysis', 'breakdown', 
            'what happened', 'latest news', 'update', 'highlights',
            'reviews', 'commentary', 'discussion about', 'explained',
            'everything you need to know', 'top 10', 'best of',
            'zipdeal', 'autohub', 'car', 'automotive'
        ]
        for keyword in heavy_negative_keywords:
            if keyword in title:
                score -= 40
        
        # Strategic content in description
        if any(keyword in description for keyword in strategic_keywords):
            score += 8
        
        # Leader name in description
        if leader_name.lower() in description:
            score += 8
        
        # Penalize very short descriptions
        if len(description) < 100:
            score -= 8
        
        # Bonus for high-engagement content
        like_count = video_info.get('like_count', 0)
        if like_count > 1000:
            score += 5
        
        # Ensure score is within bounds
        return max(0, min(100, score))
    
    def filter_and_rank_videos(self, videos: List[Dict[str, Any]], leader_name: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Filter and rank videos based on relevance score.
        
        Args:
            videos (List[Dict[str, Any]]): List of videos
            leader_name (str): Name of the leader
            company_name (str): Name of the company
            
        Returns:
            List[Dict[str, Any]]: Filtered and ranked videos
        """
        scored_videos = []
        
        for video in videos:
            score = self.score_video_relevance(video, leader_name, company_name)
            video['relevance_score'] = score
            scored_videos.append(video)
        
        # Filter out low-scoring videos and sort by score
        filtered_videos = [v for v in scored_videos if v['relevance_score'] >= 30]
        filtered_videos.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return filtered_videos


# Global searcher instance
interview_searcher = InterviewSearcher()


def search_interviews_for_leaders(leaders: List[Dict[str, str]], company_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for interviews for a list of leaders.
    
    Args:
        leaders (List[Dict[str, str]]): List of leaders
        company_name (str): Company name
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Interview results by leader
    """
    return interview_searcher.search_multiple_leaders(leaders, company_name)


if __name__ == "__main__":
    # Test the interview searcher
    test_leaders = [
        {"name": "Tim Cook", "title": "CEO"},
        {"name": "Jeff Williams", "title": "COO"}
    ]
    
    print("🧪 Testing Interview Search...")
    results = search_interviews_for_leaders(test_leaders, "Apple")
    
    for leader_name, interviews in results.items():
        print(f"\n{leader_name}:")
        for interview in interviews[:3]:  # Show first 3
            print(f"  - {interview['title']}")
            print(f"    {interview['url']}") 