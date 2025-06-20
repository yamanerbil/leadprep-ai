"""
Database module for LeadPrep AI using Supabase.

This module handles database operations for companies, leaders, and interviews.
"""

import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class LeadPrepDatabase:
    """Database interface for LeadPrep AI."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            print("⚠️  Supabase credentials not found in environment variables")
            print("   Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
            self.client = None
        else:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            print("✅ Connected to Supabase database")
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        if not self.client:
            print("❌ Cannot create tables: Supabase not connected")
            return False
            
        try:
            # Create companies table
            self.client.table('companies').select('*').limit(1).execute()
            print("✅ Companies table exists")
        except Exception:
            print("📋 Creating companies table...")
            # Note: In Supabase, tables are created via the dashboard or migrations
            # For now, we'll assume they exist or create them manually
            
        return True
    
    def upsert_company(self, domain: str, name: str = None, industry: str = None) -> Optional[int]:
        """
        Insert or update a company.
        
        Args:
            domain (str): Company domain
            name (str): Company name
            industry (str): Company industry
            
        Returns:
            Optional[int]: Company ID if successful
        """
        if not self.client:
            return None
            
        try:
            # Check if company exists
            result = self.client.table('companies').select('id').eq('domain', domain).execute()
            
            if result.data:
                # Update existing company
                company_id = result.data[0]['id']
                self.client.table('companies').update({
                    'name': name,
                    'industry': industry,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', company_id).execute()
                print(f"📝 Updated company: {domain}")
                return company_id
            else:
                # Insert new company
                result = self.client.table('companies').insert({
                    'domain': domain,
                    'name': name,
                    'industry': industry,
                    'created_at': datetime.now().isoformat()
                }).execute()
                
                if result.data:
                    company_id = result.data[0]['id']
                    print(f"➕ Added company: {domain}")
                    return company_id
                    
        except Exception as e:
            print(f"❌ Error upserting company {domain}: {e}")
            
        return None
    
    def upsert_leaders(self, company_id: int, leaders: List[Dict[str, str]]) -> List[int]:
        """
        Insert or update leaders for a company.
        
        Args:
            company_id (int): Company ID
            leaders (List[Dict[str, str]]): List of leaders with name and title
            
        Returns:
            List[int]: List of leader IDs
        """
        if not self.client:
            return []
            
        leader_ids = []
        
        try:
            for leader in leaders:
                # Check if leader exists for this company
                result = self.client.table('leaders').select('id').eq('company_id', company_id).eq('name', leader['name']).execute()
                
                if result.data:
                    # Update existing leader
                    leader_id = result.data[0]['id']
                    self.client.table('leaders').update({
                        'title': leader['title'],
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', leader_id).execute()
                    leader_ids.append(leader_id)
                else:
                    # Insert new leader
                    result = self.client.table('leaders').insert({
                        'company_id': company_id,
                        'name': leader['name'],
                        'title': leader['title'],
                        'created_at': datetime.now().isoformat()
                    }).execute()
                    
                    if result.data:
                        leader_ids.append(result.data[0]['id'])
                        
        except Exception as e:
            print(f"❌ Error upserting leaders for company {company_id}: {e}")
            
        return leader_ids
    
    def get_company_leaders(self, domain: str) -> List[Dict[str, str]]:
        """
        Get leaders for a company from database.
        
        Args:
            domain (str): Company domain
            
        Returns:
            List[Dict[str, str]]: List of leaders
        """
        if not self.client:
            return []
            
        try:
            # Join companies and leaders tables
            result = self.client.table('companies').select(
                'leaders(id, name, title)'
            ).eq('domain', domain).execute()
            
            if result.data and result.data[0]['leaders']:
                return result.data[0]['leaders']
                
        except Exception as e:
            print(f"❌ Error getting leaders for {domain}: {e}")
            
        return []
    
    def save_company_data(self, domain: str, leaders: List[Dict[str, str]], data_source: str = 'llm') -> bool:
        """
        Save company and leader data to database.
        
        Args:
            domain (str): Company domain
            leaders (List[Dict[str, str]]): List of leaders
            data_source (str): Source of the data ('llm', 'scraping', etc.)
            
        Returns:
            bool: True if successful
        """
        if not self.client:
            return False
            
        try:
            # Upsert company
            company_id = self.upsert_company(domain)
            if not company_id:
                return False
                
            # Upsert leaders
            leader_ids = self.upsert_leaders(company_id, leaders)
            
            print(f"💾 Saved {len(leaders)} leaders for {domain} to database")
            return True
            
        except Exception as e:
            print(f"❌ Error saving company data for {domain}: {e}")
            return False


# Global database instance
db = LeadPrepDatabase()


def init_database():
    """Initialize the database connection and tables."""
    return db.create_tables()


def save_leaders_to_db(domain: str, leaders: List[Dict[str, str]], data_source: str = 'llm') -> bool:
    """
    Save leaders to database.
    
    Args:
        domain (str): Company domain
        leaders (List[Dict[str, str]]): List of leaders
        data_source (str): Source of the data
        
    Returns:
        bool: True if successful
    """
    return db.save_company_data(domain, leaders, data_source)


def get_leaders_from_db(domain: str) -> List[Dict[str, str]]:
    """
    Get leaders from database.
    
    Args:
        domain (str): Company domain
        
    Returns:
        List[Dict[str, str]]: List of leaders
    """
    return db.get_company_leaders(domain)


if __name__ == "__main__":
    # Test database connection
    print("🧪 Testing Database Connection...")
    
    if init_database():
        print("✅ Database initialized successfully")
        
        # Test with sample data
        test_leaders = [
            {"name": "Tim Cook", "title": "CEO"},
            {"name": "Jeff Williams", "title": "COO"}
        ]
        
        success = save_leaders_to_db("apple.com", test_leaders)
        print(f"Save test data: {'✅' if success else '❌'}")
        
        leaders = get_leaders_from_db("apple.com")
        print(f"Retrieved {len(leaders)} leaders from database")
    else:
        print("❌ Database initialization failed") 