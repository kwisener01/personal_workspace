import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CalendarAirtableServer:
    def __init__(self):
        self.google_calendar_token = os.getenv('GOOGLE_CALENDAR_TOKEN')
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
        
    async def get_google_events(self, start_time: str = None, end_time: str = None):
        """Fetch events from Google Calendar"""
        headers = {
            'Authorization': f'Bearer {self.google_calendar_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'timeMin': start_time or datetime.utcnow().isoformat() + 'Z',
            'timeMax': end_time or (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z',
            'singleEvents': 'true',
            'orderBy': 'startTime'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                return []
    
    async def create_google_event(self, event_data: Dict[str, Any]):
        """Create a new Google Calendar event"""
        headers = {
            'Authorization': f'Bearer {self.google_calendar_token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                headers=headers,
                json=event_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
    async def get_airtable_records(self, table_name: str, filter_formula: str = None):
        """Fetch records from Airtable"""
        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {}
        if filter_formula:
            params['filterByFormula'] = filter_formula
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'https://api.airtable.com/v0/{self.airtable_base_id}/{table_name}',
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('records', [])
                return []
    
    async def create_airtable_record(self, table_name: str, fields: Dict[str, Any]):
        """Create a new Airtable record"""
        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'fields': fields
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'https://api.airtable.com/v0/{self.airtable_base_id}/{table_name}',
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
