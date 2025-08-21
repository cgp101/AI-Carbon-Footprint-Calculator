"""
Data Storage Module
Handles persistent storage of carbon footprint entries and user data
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import pandas as pd
from pathlib import Path

class DataStorage:
    def __init__(self, db_path: str = "carbon_footprint.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_created TEXT NOT NULL,
                category TEXT NOT NULL,
                item_type TEXT NOT NULL,
                description TEXT,
                quantity REAL,
                unit TEXT,
                carbon_footprint REAL NOT NULL,
                amount_spent REAL,
                source TEXT DEFAULT 'manual',
                confidence REAL DEFAULT 1.0,
                metadata TEXT
            )
        ''')
        
        # Create user_settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY,
                setting_name TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create monthly_summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                category TEXT NOT NULL,
                total_emissions REAL NOT NULL,
                entry_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(year, month, category)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_entry(self, category: str, item_type: str, quantity: float, 
                 carbon_footprint: float, description: str = None, 
                 unit: str = None, amount_spent: float = None, 
                 source: str = 'manual', confidence: float = 1.0, 
                 metadata: Dict = None) -> int:
        """
        Add a new carbon footprint entry
        
        Args:
            category: Category of the entry
            item_type: Specific type within category
            quantity: Quantity/amount
            carbon_footprint: Calculated carbon footprint
            description: Optional description
            unit: Unit of measurement
            amount_spent: Money spent (if applicable)
            source: Source of data ('manual', 'ocr', 'api')
            confidence: Confidence score (0-1)
            metadata: Additional metadata as dictionary
            
        Returns:
            ID of the created entry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO entries 
            (date_created, category, item_type, description, quantity, unit, 
             carbon_footprint, amount_spent, source, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            category,
            item_type,
            description,
            quantity,
            unit,
            carbon_footprint,
            amount_spent,
            source,
            confidence,
            json.dumps(metadata) if metadata else None
        ))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update monthly summary
        self._update_monthly_summary(category, carbon_footprint)
        
        return entry_id
    
    def get_entries(self, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None, 
                   category: Optional[str] = None,
                   limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve entries with optional filtering
        
        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            category: Category filter
            limit: Maximum number of entries to return
            
        Returns:
            List of entry dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM entries WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date_created >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date_created <= ?"
            params.append(end_date)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY date_created DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        entries = []
        
        for row in cursor.fetchall():
            entry = dict(zip(columns, row))
            if entry['metadata']:
                entry['metadata'] = json.loads(entry['metadata'])
            entries.append(entry)
        
        conn.close()
        return entries
    
    def get_category_totals(self, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> Dict[str, float]:
        """
        Get total carbon footprint by category
        
        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            
        Returns:
            Dictionary with category totals
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT category, SUM(carbon_footprint) as total
            FROM entries WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += " AND date_created >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date_created <= ?"
            params.append(end_date)
        
        query += " GROUP BY category"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        totals = {
            'transport': 0.0,
            'food': 0.0,
            'appliances': 0.0,
            'entertainment': 0.0,
            'others': 0.0
        }
        
        for category, total in results:
            if category in totals:
                totals[category] = total
        
        return totals
    
    def get_monthly_trend(self, months: int = 12) -> pd.DataFrame:
        """
        Get monthly carbon footprint trends
        
        Args:
            months: Number of months to include
            
        Returns:
            DataFrame with monthly trends
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                strftime('%Y-%m', date_created) as month,
                category,
                SUM(carbon_footprint) as total_emissions,
                COUNT(*) as entry_count
            FROM entries 
            WHERE date_created >= date('now', '-{} months')
            GROUP BY strftime('%Y-%m', date_created), category
            ORDER BY month DESC, category
        '''.format(months)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics
        
        Returns:
            Dictionary with various statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM entries")
        total_entries = cursor.fetchone()[0]
        
        # Total carbon footprint
        cursor.execute("SELECT SUM(carbon_footprint) FROM entries")
        total_carbon = cursor.fetchone()[0] or 0
        
        # Average daily emissions (last 30 days)
        cursor.execute('''
            SELECT AVG(daily_total) FROM (
                SELECT DATE(date_created) as date, SUM(carbon_footprint) as daily_total
                FROM entries 
                WHERE date_created >= date('now', '-30 days')
                GROUP BY DATE(date_created)
            )
        ''')
        avg_daily = cursor.fetchone()[0] or 0
        
        # Most common category
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM entries 
            GROUP BY category 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        most_common_category = result[0] if result else 'none'
        
        # Monthly average
        cursor.execute('''
            SELECT AVG(monthly_total) FROM (
                SELECT strftime('%Y-%m', date_created) as month, 
                       SUM(carbon_footprint) as monthly_total
                FROM entries 
                GROUP BY strftime('%Y-%m', date_created)
            )
        ''')
        avg_monthly = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'total_carbon_footprint': total_carbon,
            'average_daily_emissions': avg_daily,
            'average_monthly_emissions': avg_monthly,
            'most_common_category': most_common_category
        }
    
    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete an entry by ID
        
        Args:
            entry_id: ID of the entry to delete
            
        Returns:
            True if deleted successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def update_entry(self, entry_id: int, **kwargs) -> bool:
        """
        Update an existing entry
        
        Args:
            entry_id: ID of the entry to update
            **kwargs: Fields to update
            
        Returns:
            True if updated successfully
        """
        if not kwargs:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build update query
        set_clauses = []
        params = []
        
        for field, value in kwargs.items():
            if field in ['category', 'item_type', 'description', 'quantity', 
                        'unit', 'carbon_footprint', 'amount_spent', 'source', 'confidence']:
                set_clauses.append(f"{field} = ?")
                params.append(value)
            elif field == 'metadata' and isinstance(value, dict):
                set_clauses.append("metadata = ?")
                params.append(json.dumps(value))
        
        if not set_clauses:
            conn.close()
            return False
        
        params.append(entry_id)
        query = f"UPDATE entries SET {', '.join(set_clauses)} WHERE id = ?"
        
        cursor.execute(query, params)
        updated = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return updated
    
    def export_data(self, format: str = 'csv', file_path: Optional[str] = None) -> str:
        """
        Export data to file
        
        Args:
            format: Export format ('csv', 'json')
            file_path: Output file path
            
        Returns:
            Path to exported file
        """
        entries = self.get_entries()
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"carbon_footprint_export_{timestamp}.{format}"
        
        if format.lower() == 'csv':
            df = pd.DataFrame(entries)
            df.to_csv(file_path, index=False)
        elif format.lower() == 'json':
            with open(file_path, 'w') as f:
                json.dump(entries, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return file_path
    
    def _update_monthly_summary(self, category: str, carbon_footprint: float):
        """
        Update monthly summary statistics
        
        Args:
            category: Category of the entry
            carbon_footprint: Carbon footprint value
        """
        now = datetime.now()
        year = now.year
        month = now.month
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if summary exists
        cursor.execute('''
            SELECT id, total_emissions, entry_count 
            FROM monthly_summaries 
            WHERE year = ? AND month = ? AND category = ?
        ''', (year, month, category))
        
        result = cursor.fetchone()
        
        if result:
            # Update existing summary
            summary_id, current_total, current_count = result
            cursor.execute('''
                UPDATE monthly_summaries 
                SET total_emissions = ?, entry_count = ?
                WHERE id = ?
            ''', (current_total + carbon_footprint, current_count + 1, summary_id))
        else:
            # Create new summary
            cursor.execute('''
                INSERT INTO monthly_summaries 
                (year, month, category, total_emissions, entry_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (year, month, category, carbon_footprint, 1, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_user_setting(self, setting_name: str, default_value: Any = None) -> Any:
        """
        Get a user setting
        
        Args:
            setting_name: Name of the setting
            default_value: Default value if setting doesn't exist
            
        Returns:
            Setting value
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT setting_value FROM user_settings WHERE setting_name = ?",
            (setting_name,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                return result[0]
        
        return default_value
    
    def set_user_setting(self, setting_name: str, setting_value: Any):
        """
        Set a user setting
        
        Args:
            setting_name: Name of the setting
            setting_value: Value to set
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        value_str = json.dumps(setting_value) if not isinstance(setting_value, str) else setting_value
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_settings 
            (setting_name, setting_value, updated_at)
            VALUES (?, ?, ?)
        ''', (setting_name, value_str, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_all_entries_df(self) -> pd.DataFrame:
        """
        Get all entries as a pandas DataFrame
        
        Returns:
            DataFrame containing all carbon footprint entries
        """
        entries = self.get_entries()
        
        if not entries:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'id', 'date_created', 'category', 'item_type', 'description',
                'quantity', 'unit', 'carbon_footprint', 'amount_spent', 
                'source', 'confidence', 'metadata'
            ])
        
        df = pd.DataFrame(entries)
        
        # Convert date_created to datetime for better analytics
        df['date_created'] = pd.to_datetime(df['date_created'])
        
        # Create 'date' column for compatibility with analytics
        df['date'] = df['date_created'].dt.date
        
        # Ensure numeric columns are properly typed
        df['carbon_footprint'] = pd.to_numeric(df['carbon_footprint'], errors='coerce').fillna(0)
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        df['amount_spent'] = pd.to_numeric(df['amount_spent'], errors='coerce')
        df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce').fillna(1.0)
        
        return df 