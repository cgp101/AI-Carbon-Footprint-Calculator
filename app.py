"""
AI-Powered Carbon Footprint Calculator
Main Streamlit application with text input, photo upload, and categorization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
import json
from PIL import Image
import io
from carbon_calculator import CarbonCalculator
from image_processor import ImageProcessor
from data_storage import DataStorage
from predictive_analytics import PredictiveAnalytics
from smart_recommendations import SmartRecommendations
from integrations import IntegrationManager, FitnessIntegration, SmartHomeIntegration, WeatherIntegration
from location_tracker import LocationTracker
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import os

# Configure Streamlit page
st.set_page_config(
    page_title="🌍 AI-Powered Carbon Footprint Calculator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_calculator_and_processor():
    calculator = CarbonCalculator()
    image_processor = ImageProcessor()
    predictive_analytics = PredictiveAnalytics()
    smart_recommendations = SmartRecommendations()
    integration_manager = IntegrationManager()
    location_tracker = LocationTracker()
    return calculator, image_processor, predictive_analytics, smart_recommendations, integration_manager, location_tracker

# Initialize DataStorage without caching to prevent database issues
def init_storage():
    return DataStorage()

calculator, image_processor, predictive_analytics, smart_recommendations, integration_manager, location_tracker = init_calculator_and_processor()
storage = init_storage()

# Check if photo upload (OpenAI) is available
try:
    from config import get_openai_key
    openai_key = get_openai_key()
    photo_upload_available = openai_key and openai_key != "your-openai-api-key-here" and len(openai_key) > 10
except ImportError:
    photo_upload_available = False

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .category-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
    }
    .recommendation {
        background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-left: 4px solid #4caf50;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">🌍 AI Carbon Footprint Calculator</h1>', unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    page = st.selectbox("Choose a page:", [
        "📊 Dashboard",
        "✍️ Manual Entry", 
        "📸 Photo Upload",
        "📈 Analytics",
        "🤖 AI Insights & Recommendations",
        "🔗 Integrations",
        "📍 Location Tracking",
        "⚙️ Settings"
    ])

if page == "📊 Dashboard":
    st.header("Dashboard Overview")
    
    # Add refresh button to ensure fresh data
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.write("Real-time carbon footprint statistics")
    with col_header2:
        if st.button("🔄 Refresh Data", key="dashboard_refresh"):
            st.rerun()
    
    # Force fresh data by reinitializing storage if needed
    try:
        # Get statistics with error handling
        stats = storage.get_statistics()
        category_totals = storage.get_category_totals()
        total_emissions = sum(category_totals.values())
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Trying to refresh database connection...")
        # Reinitialize storage
        storage = DataStorage()
    stats = storage.get_statistics()
    category_totals = storage.get_category_totals()
    total_emissions = sum(category_totals.values())
    
    # Display last updated time
    st.caption(f"📊 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    

    
    # Check for recent additions and display notification
    if st.session_state.get('new_data_added', False):
        st.success(f"""
        🎉 **Recent Update Detected!** 
        - Entry ID: {st.session_state.get('last_entry_id', 'N/A')}
        - Added: {st.session_state.get('last_carbon_footprint', 0):.2f} kg CO₂
        - The statistics below include your latest trip data!
        """)
        
        # Clear the flag after showing
        if st.button("✅ Got it!", key="clear_notification"):
            st.session_state.new_data_added = False
            st.rerun()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['total_entries']}</h3>
            <p>Total Entries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{total_emissions:.1f} kg</h3>
            <p>Total CO₂ Emissions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['average_daily_emissions']:.1f} kg</h3>
            <p>Daily Average</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['average_monthly_emissions']:.1f} kg</h3>
            <p>Monthly Average</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Category breakdown
    if total_emissions > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Carbon Footprint by Category")
            
            # Pie chart
            fig = px.pie(
                values=list(category_totals.values()),
                names=list(category_totals.keys()),
                title="Emissions Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Recommendations")
            recommendations = calculator.get_recommendations(category_totals)
            
            for rec in recommendations[:3]:  # Show top 3 recommendations
                st.markdown(f"""
                <div class="recommendation">
                    {rec}
                </div>
                """, unsafe_allow_html=True)
    
    # Recent entries
    st.subheader("Recent Entries")
    recent_entries = storage.get_entries(limit=5)
    
    if recent_entries:
        df = pd.DataFrame(recent_entries)
        display_columns = ['date_created', 'category', 'item_type', 'quantity', 'carbon_footprint']
        df_display = df[display_columns].copy()
        df_display['date_created'] = pd.to_datetime(df_display['date_created']).dt.strftime('%Y-%m-%d %H:%M')
        df_display['carbon_footprint'] = df_display['carbon_footprint'].round(2)
        df_display.columns = ['Date', 'Category', 'Type', 'Quantity', 'CO₂ (kg)']
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No entries yet. Start by adding your first carbon footprint entry!")

elif page == "✍️ Manual Entry":
    st.header("Manual Entry")
    
    # Two input methods
    input_method = st.radio("Choose input method:", ["Natural Language", "Structured Form"])
    
    if input_method == "Natural Language":
        st.subheader("🎯 General Activity Input")
        st.info("💡 **Any Activity Welcome!** Describe any activity in your own words - we'll help you track the carbon impact!")
        
        # Initialize text input in session state if not exists
        if 'text_input_value' not in st.session_state:
            st.session_state.text_input_value = ""
        
        # More flexible and general text input
        text_input = st.text_area(
            "Describe what you did",
            value=st.session_state.text_input_value,
            placeholder="e.g., 'went shopping', 'had dinner', 'used the car today', 'worked from home', 'bought groceries', 'cooked pasta'",
            height=120,
            key="activity_text_input",
            help="Describe any activity - no need to include specific amounts or distances unless you know them"
        )
        
        # Additional context (optional)
        col1, col2 = st.columns(2)
        
        with col1:
            context_details = st.text_input(
                "Any additional details? (optional)",
                placeholder="e.g., 'by car', 'for 2 hours', 'with family', 'electric vehicle'",
                help="Add any extra context that might help estimate carbon impact"
            )
        
        with col2:
            rough_amount = st.text_input(
                "Rough amount/time? (optional)", 
                placeholder="e.g., '1 hour', 'about 20 km', '3 people', 'half day'",
                help="Any rough quantities, distances, or durations if you know them"
            )
        
        # Update session state when text changes
        if text_input != st.session_state.text_input_value:
            st.session_state.text_input_value = text_input
        
        if st.button("🤖 Analyze Activity", type="primary"):
            if text_input.strip():
                with st.spinner("🧠 Understanding your activity..."):
                    # Combine all inputs for better context
                    full_description = text_input.strip()
                    if context_details.strip():
                        full_description += f" ({context_details.strip()})"
                    if rough_amount.strip():
                        full_description += f" - {rough_amount.strip()}"
                    
                    # Try the existing parser first (might catch specific patterns)
                    entries = calculator.parse_text_entry(full_description)
                    
                    if entries:
                        # Existing parser found something
                        st.session_state.parsed_entries = entries
                        st.session_state.original_text = full_description
                        st.success(f"✅ **Found {len(entries)} activities!** The system recognized specific patterns in your description.")
                        
                    else:
                        # No specific patterns found - create a general entry
                        st.info("🤔 **Creating general entry...** The system will estimate carbon impact based on your description.")
                        
                        # Intelligent categorization based on keywords
                        description_lower = full_description.lower()
                        
                        # Smart category detection
                        if any(word in description_lower for word in ['drove', 'car', 'bus', 'train', 'walk', 'bike', 'taxi', 'uber', 'flight', 'plane', 'travel', 'commute', 'trip']):
                            category = 'transport'
                            item_type = 'general_transport'
                            default_emission = 2.0  # kg CO2
                        elif any(word in description_lower for word in ['ate', 'food', 'meal', 'lunch', 'dinner', 'breakfast', 'restaurant', 'cook', 'beef', 'chicken', 'pizza']):
                            category = 'food'
                            item_type = 'general_meal'
                            default_emission = 1.5  # kg CO2
                        elif any(word in description_lower for word in ['electricity', 'heat', 'air conditioning', 'tv', 'computer', 'lights', 'appliance', 'washing', 'dryer']):
                            category = 'appliances'
                            item_type = 'general_energy_use'
                            default_emission = 1.0  # kg CO2
                        elif any(word in description_lower for word in ['shopping', 'bought', 'purchase', 'store', 'mall', 'online', 'amazon', 'clothes', 'shoes']):
                            category = 'others'
                            item_type = 'general_shopping'
                            default_emission = 1.5  # kg CO2
                        elif any(word in description_lower for word in ['movie', 'cinema', 'concert', 'game', 'streaming', 'netflix', 'entertainment', 'sport']):
                            category = 'entertainment'
                            item_type = 'general_entertainment'
                            default_emission = 0.8  # kg CO2
                        else:
                            # Default catch-all
                            category = 'others'
                            item_type = 'general_activity'
                            default_emission = 1.0  # kg CO2
                        
                        # Try to extract quantity hints from rough_amount
                        estimated_quantity = 1.0
                        unit = 'activity'
                        
                        if rough_amount.strip():
                            amount_lower = rough_amount.lower()
                            # Look for numbers
                            import re
                            numbers = re.findall(r'\d+(?:\.\d+)?', amount_lower)
                            if numbers:
                                estimated_quantity = float(numbers[0])
                                
                                # Adjust unit based on context
                                if any(word in amount_lower for word in ['km', 'mile', 'kilometer']):
                                    unit = 'km'
                                    if category == 'transport':
                                        default_emission = estimated_quantity * 0.21  # per km for car
                                elif any(word in amount_lower for word in ['hour', 'hr', 'min']):
                                    unit = 'hours'
                                    if 'min' in amount_lower:
                                        estimated_quantity = estimated_quantity / 60  # convert to hours
                                elif any(word in amount_lower for word in ['people', 'person']):
                                    unit = 'people'
                                    default_emission = default_emission * estimated_quantity
                                    estimated_quantity = 1.0  # normalize back to per-activity
                        
                        # Create the general entry
                        general_entry = {
                            'category': category,
                            'item_type': item_type,
                            'quantity': estimated_quantity,
                            'carbon_footprint': default_emission,
                            'unit': unit,
                            'description': full_description,
                            'confidence': 'estimated'
                        }
                        
                        st.session_state.parsed_entries = [general_entry]
                        st.session_state.original_text = full_description
                        
                        # Show estimation details
                        st.success("✅ **Activity analyzed successfully!**")
                        
                        col_info1, col_info2, col_info3 = st.columns(3)
                        with col_info1:
                            st.metric("📂 Category", category.title())
                        with col_info2:
                            st.metric("📊 Estimated CO₂", f"{default_emission:.1f} kg")
                        with col_info3:
                            st.metric("🎯 Confidence", "Estimated")
                        
                        st.info(f"💡 **How we estimated:** Based on keywords in your description, we categorized this as **{category}** "
                               f"and estimated **{default_emission:.1f} kg CO₂**. You can adjust this before saving if needed.")
                        
            else:
                st.warning("⚠️ Please describe your activity first.")
        
        # Display parsed entries from session state (persists between button clicks)
        if 'parsed_entries' in st.session_state and st.session_state.parsed_entries:
            entries = st.session_state.parsed_entries
            text_input = st.session_state.original_text
            
            # Display parsed entries
            for i, entry in enumerate(entries):
                with st.expander(f"Activity {i+1}: {entry['item_type'].replace('_', ' ').title()}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Category:** {entry['category'].title()}")
                        st.write(f"**Type:** {entry['item_type'].replace('_', ' ').title()}")
                    
                    with col2:
                        st.write(f"**Quantity:** {entry['quantity']}")
                        st.write(f"**Carbon Footprint:** {entry['carbon_footprint']:.2f} kg CO₂")
                    
                    with col3:
                        st.write(f"**Status:** Ready to save")
            
            # Action buttons for all activities
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("💾 Save All Activities", type="primary"):
                    try:
                        with st.spinner("Saving activities to database..."):
                            saved_entries = []
                            saved_count = 0
                            total_saved_co2 = 0
                            
                            for entry in entries:
                                # Save to database and get the entry ID
                                entry_id = storage.add_entry(
                                    category=entry['category'],
                                    item_type=entry['item_type'],
                                    quantity=entry['quantity'],
                                    carbon_footprint=entry['carbon_footprint'],
                                    description=text_input,
                                    source='manual_text'
                                )
                                
                                # Track what was saved
                                saved_entries.append({
                                    'id': entry_id,
                                    'category': entry['category'],
                                    'item_type': entry['item_type'],
                                    'quantity': entry['quantity'],
                                    'co2': entry['carbon_footprint']
                                })
                                saved_count += 1
                                total_saved_co2 += entry['carbon_footprint']
                        
                        # Show detailed success message
                        st.success("🎉 **Activities Successfully Saved!**")
                        
                        # Show confirmation details
                        with st.expander("📋 Saved Activities Details", expanded=True):
                            st.write(f"**Total Activities Saved:** {saved_count}")
                            st.write(f"**Total Carbon Footprint:** {total_saved_co2:.2f} kg CO₂")
                            st.write("**Activities:**")
                            
                            for i, saved_entry in enumerate(saved_entries, 1):
                                st.write(f"{i}. **{saved_entry['category'].title()}** - "
                                       f"{saved_entry['item_type'].replace('_', ' ').title()} "
                                       f"(Qty: {saved_entry['quantity']}, "
                                       f"CO₂: {saved_entry['co2']:.2f} kg) "
                                       f"[ID: {saved_entry['id']}]")
                            
                            st.info("💡 **Database Updated!** Your activities have been permanently saved and will appear in your dashboard and analytics.")
                        
                        # Verify database was updated
                        try:
                            recent_entries = storage.get_entries(limit=saved_count)
                            if len(recent_entries) >= saved_count:
                                st.success("✅ **Database Verification:** All entries confirmed in database!")
                            else:
                                st.warning("⚠️ Database verification: Some entries may not have been saved properly.")
                        except Exception as e:
                            st.warning(f"⚠️ Could not verify database update: {str(e)}")
                        
                        # Clear session state after successful save
                        del st.session_state.parsed_entries
                        del st.session_state.original_text
                        st.session_state.text_input_value = "" # Clear text input after save
                        
                        # Wait a moment before rerunning to show the messages
                        import time
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ **Error saving activities:** {str(e)}")
                        st.error("Please try again or contact support if the problem persists.")
                        st.info("💡 **Troubleshooting:** Make sure you have write permissions and sufficient disk space.")
            
            with col2:
                if st.button("✏️ Edit Activities"):
                    st.session_state.edit_mode = True
                    st.rerun()
                
                if st.button("🗑️ Clear Activities"):
                    del st.session_state.parsed_entries
                    del st.session_state.original_text
                    st.session_state.text_input_value = ""  # Clear text input
                    st.rerun()
            
            with col3:
                total_co2 = sum(entry['carbon_footprint'] for entry in entries)
                st.metric("Total Carbon Footprint", f"{total_co2:.2f} kg CO₂")
            
            # Edit mode
            if st.session_state.get('edit_mode', False):
                st.markdown("---")
                st.subheader("✏️ Edit Activities")
                
                edited_entries = []
                for i, entry in enumerate(entries):
                    with st.expander(f"Edit Activity {i+1}: {entry['item_type'].replace('_', ' ').title()}", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            new_category = st.selectbox(
                                "Category", 
                                ["transport", "food", "appliances", "entertainment", "others"],
                                index=["transport", "food", "appliances", "entertainment", "others"].index(entry['category']),
                                key=f"edit_cat_{i}"
                            )
                            
                            item_options = {
                                'transport': ['walk', 'car_petrol', 'car_diesel', 'bus', 'train', 'plane_domestic', 'plane_international', 'taxi', 'metro'],
                                'food': ['beef', 'chicken', 'pork', 'fish', 'vegetables', 'dairy', 'rice', 'restaurant_meal', 'fast_food'],
                                'appliances': ['electricity', 'natural_gas', 'heating_oil', 'washing_machine', 'dishwasher', 'air_conditioning', 'heating'],
                                'entertainment': ['streaming', 'gaming', 'movie_theater', 'concert', 'sports_event', 'shopping'],
                                'others': ['clothing', 'electronics', 'furniture', 'books', 'cosmetics']
                            }
                            
                            new_item_type = st.selectbox(
                                "Item Type",
                                item_options[new_category],
                                index=item_options[new_category].index(entry['item_type']) if entry['item_type'] in item_options[new_category] else 0,
                                key=f"edit_item_{i}"
                            )
                        
                        with col2:
                            new_quantity = st.number_input(
                                "Quantity", 
                                value=float(entry['quantity']), 
                                min_value=0.0, 
                                step=0.1,
                                key=f"edit_qty_{i}"
                            )
                        
                        with col3:
                            new_co2 = calculator.calculate_carbon_footprint(new_category, new_item_type, new_quantity)
                            st.metric("Updated CO₂", f"{new_co2:.2f} kg")
                        
                        edited_entries.append({
                            'category': new_category,
                            'item_type': new_item_type,
                            'quantity': new_quantity,
                            'carbon_footprint': new_co2
                        })
                
                # Save edited entries
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save Edited Activities", type="primary"):
                        try:
                            with st.spinner("Saving edited activities to database..."):
                                saved_entries = []
                                saved_count = 0
                                total_saved_co2 = 0
                                
                                for entry in edited_entries:
                                    # Save to database and get the entry ID
                                    entry_id = storage.add_entry(
                                        category=entry['category'],
                                        item_type=entry['item_type'],
                                        quantity=entry['quantity'],
                                        carbon_footprint=entry['carbon_footprint'],
                                        description=text_input,
                                        source='manual_text_edited'
                                    )
                                    
                                    # Track what was saved
                                    saved_entries.append({
                                        'id': entry_id,
                                        'category': entry['category'],
                                        'item_type': entry['item_type'],
                                        'quantity': entry['quantity'],
                                        'co2': entry['carbon_footprint']
                                    })
                                    saved_count += 1
                                    total_saved_co2 += entry['carbon_footprint']
                            
                            # Show detailed success message
                            st.success("🎉 **Edited Activities Successfully Saved!**")
                            
                            # Show confirmation details
                            with st.expander("📋 Saved Edited Activities Details", expanded=True):
                                st.write(f"**Total Edited Activities Saved:** {saved_count}")
                                st.write(f"**Total Carbon Footprint:** {total_saved_co2:.2f} kg CO₂")
                                st.write("**Edited Activities:**")
                                
                                for i, saved_entry in enumerate(saved_entries, 1):
                                    st.write(f"{i}. **{saved_entry['category'].title()}** - "
                                           f"{saved_entry['item_type'].replace('_', ' ').title()} "
                                           f"(Qty: {saved_entry['quantity']}, "
                                           f"CO₂: {saved_entry['co2']:.2f} kg) "
                                           f"[ID: {saved_entry['id']}]")
                                
                                st.info("💡 **Database Updated!** Your edited activities have been permanently saved.")
                            
                        
                            
                            # Verify database was updated
                            try:
                                recent_entries = storage.get_entries(limit=saved_count)
                                if len(recent_entries) >= saved_count:
                                    st.success("✅ **Database Verification:** All edited entries confirmed in database!")
                                else:
                                    st.warning("⚠️ Database verification: Some entries may not have been saved properly.")
                            except Exception as e:
                                st.warning(f"⚠️ Could not verify database update: {str(e)}")
                            
                            # Exit edit mode and refresh
                            st.session_state.edit_mode = False
                            
                            # Clear text input and parsed entries after successful save
                            if 'parsed_entries' in st.session_state:
                                del st.session_state.parsed_entries
                            if 'original_text' in st.session_state:
                                del st.session_state.original_text
                            st.session_state.text_input_value = ""
                            
                            # Wait a moment before rerunning to show the messages
                            import time
                            time.sleep(2)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ **Error saving edited activities:** {str(e)}")
                            st.error("Please try again or contact support if the problem persists.")
                            st.info("💡 **Troubleshooting:** Make sure you have write permissions and sufficient disk space.")
                
                with col2:
                    if st.button("❌ Cancel Edit"):
                        st.session_state.edit_mode = False
                        st.rerun()
    
    else:  # Structured Form
        st.subheader("Structured Entry Form")
        
        # Category and Item Type selection (outside form for dynamic updates)
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox("Category", [
                "transport", "food", "appliances", "entertainment", "others"
            ])
            
            # Dynamic item type based on category
            item_options = {
                'transport': ['walking', 'car_petrol', 'car_diesel', 'bus', 'train', 'plane_domestic', 'plane_international', 'taxi', 'metro'],
                'food': ['beef', 'chicken', 'pork', 'fish', 'fruits', 'vegetables', 'dairy', 'restaurant_meal', 'fast_food'],
                'appliances': ['electricity', 'natural_gas', 'heating_oil', 'washing_machine', 'dishwasher', 'air_conditioning'],
                'entertainment': ['streaming', 'gaming', 'movie_theater', 'concert', 'sports_event', 'shopping'],
                'others': ['clothing', 'electronics', 'furniture', 'books', 'cosmetics']
            }
            
            item_type = st.selectbox("Item Type", item_options[category])
        
        with col2:
            quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
            unit = st.text_input("Unit (optional)", placeholder="e.g., km, kg, hours")
        
        # Additional details in a form (these don't need dynamic updates)
        with st.form("additional_details_form"):
            col3, col4 = st.columns(2)
            
            with col3:
                amount_spent = st.number_input("Amount Spent ($)", min_value=0.0, step=0.01)
            
            with col4:
                description = st.text_area("Description (optional)")
            
            if st.form_submit_button("Calculate & Save", type="primary"):
                if quantity > 0:
                    carbon_footprint = calculator.calculate_carbon_footprint(
                        category, item_type, quantity, unit
                    )
                    
                    # Save to database
                    entry_id = storage.add_entry(
                        category=category,
                        item_type=item_type,
                        quantity=quantity,
                        carbon_footprint=carbon_footprint,
                        description=description,
                        unit=unit,
                        amount_spent=amount_spent if amount_spent > 0 else None,
                        source='manual_form'
                    )
                    
                    st.success(f"✅ Entry saved! Carbon footprint: {carbon_footprint:.2f} kg CO₂")
                else:
                    st.error("Please enter a quantity greater than 0.")

elif page == "📸 Photo Upload":
    st.header("📸 AI Receipt Scanner - Powered by OpenAI")
    
    if not photo_upload_available:
        st.error("❌ OpenAI API key required for photo upload!")
        st.info("📋 **To enable photo upload:**")
        st.write("1. Get an OpenAI API key from https://platform.openai.com/api-keys")
        
    else:
        st.info("📸 **How it works:** Upload any carbon footprint-related document (receipts, bills, tickets), and our AI will extract details and automatically calculate your carbon footprint!")
    
        uploaded_file = st.file_uploader(
            "Choose a document image...",
            type=['png', 'jpg', 'jpeg'],
            help="Upload any carbon footprint-related document: grocery receipts, restaurant bills, gas receipts, transit tickets, utility bills, shopping receipts, or service invoices."
        )
        
        if uploaded_file is not None:
            # Display the uploaded image
            image = Image.open(uploaded_file)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📷 Uploaded Image")
                st.image(image, caption="Receipt Image", use_container_width=True)
                
                # Show image info
                st.info(f"📏 **Image size:** {image.size[0]}x{image.size[1]} pixels")
                if hasattr(image_processor, 'openai_ocr') and image_processor.openai_ocr:
                    cost_estimate = image_processor.openai_ocr.get_cost_estimate(image)
                    st.info(f"💰 **Estimated cost:** ${cost_estimate:.4f}")
            
            with col2:
                st.subheader("🔍 Processing Results")
                
                if st.button("🤖 Analyze with AI", type="primary"):
                    with st.spinner("🧠 OpenAI GPT-4 Vision analyzing your receipt..."):
                        try:
                            result = image_processor.process_receipt_image(image)
                        except Exception as e:
                            st.error(f"❌ Error processing image: {str(e)}")
                            result = {'success': False, 'error': str(e)}
                        
                        # Check for OpenAI specific errors
                        if result.get('text', '').startswith('OPENAI_ERROR'):
                            st.error("❌ OpenAI Vision analysis failed!")
                            error_msg = result['text'].replace('OPENAI_ERROR: ', '')
                            st.error(f"Error: {error_msg}")
                            
                            if "api key" in error_msg.lower():
                                st.info("💡 **Solution:** Check your OpenAI API key in the sidebar")
                            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                                st.info("💡 **Solution:** Check your OpenAI account billing and usage limits")
                            else:
                                st.info("💡 **Solutions:**")
                                st.write("- Check your internet connection")
                                st.write("- Verify your OpenAI API key is valid")
                                st.write("- Try again in a moment")
                        
                        # Check if OCR is available
                        elif result.get('text', '').startswith('OCR_NOT_AVAILABLE'):
                            st.error("❌ EasyOCR is not available!")
                            st.info("📋 **To fix this:**")
                            st.code("pip install easyocr", language="bash")
                            st.warning("⚠️ Note: First-time setup requires downloading ~100MB of AI models and may take 2-3 minutes.")
                            st.info("🔧 **Alternative:** You can still use manual entry to track your carbon footprint!")
                        
                        # Check if using mock OCR
                        elif result.get('text', '').startswith('MOCK_OCR'):
                            st.warning("⚠️ Using Mock OCR (EasyOCR not available)")
                            st.info("📋 **This is simulated data for testing purposes**")
                            # Remove the MOCK_OCR prefix for processing
                            result['text'] = result['text'].replace('MOCK_OCR: ', '')
                            st.info("💡 **To use real OCR:** Install EasyOCR with `pip install easyocr`")
                            
                            # Continue with processing for mock OCR
                            if result['success']:
                                st.success("✅ Image processed successfully!")
                                
                                # Show extracted text
                                with st.expander("Extracted Text", expanded=False):
                                    st.text(result['text'])
                                
                                # Show category and confidence
                                st.write(f"**Detected Category:** {result['category'].title()}")
                                st.write(f"**Confidence:** {result['confidence']:.2f}")
                                
                                # Show amounts found
                                if result['amounts']:
                                    st.write("**Amounts Found:**")
                                    for amount_info in result['amounts']:
                                        st.write(f"- ${amount_info['amount']:.2f}: {amount_info['description']}")
                                
                                # Show total and suggested calculation
                                if result['total_amount'] > 0:
                                    # Use the categorize_expense method for automatic calculation
                                    expense_info = calculator.categorize_expense(
                                        result['text'], result['total_amount']
                                    )
                                    
                                    st.write(f"**Total Amount:** ${result['total_amount']:.2f}")
                                    st.write(f"**Estimated Carbon Footprint:** {expense_info['carbon_footprint']:.2f} kg CO₂")
                                    
                                    # Allow user to save
                                    if st.button("Save This Entry"):
                                        storage.add_entry(
                                            category=expense_info['category'],
                                            item_type=expense_info['item_type'],
                                            quantity=expense_info['estimated_quantity'],
                                            carbon_footprint=expense_info['carbon_footprint'],
                                            description=f"OCR: {result['text'][:100]}...",
                                            amount_spent=result['total_amount'],
                                            source='ocr',
                                            confidence=result['confidence'],
                                            metadata={
                                                'ocr_text': result['text'],
                                                'amounts_found': result['amounts'],
                                                'specific_data': result['specific_data']
                                            }
                                        )
                                        st.success("✅ Entry saved from OCR data!")
                                
                                # Show suggestions
                                if result['suggestions']:
                                    st.write("**AI Suggestions:**")
                                    for suggestion in result['suggestions']:
                                        st.info(suggestion)
                            else:
                                st.error(f"❌ {result['error']}")
                        
                        elif result.get('text', '').startswith('OCR_ERROR'):
                            st.error("❌ OCR processing failed!")
                            st.error(f"Error: {result['text']}")
                            st.info("💡 **Possible solutions:**")
                            st.write("- Check your internet connection (models need to download on first use)")
                            st.write("- Try restarting the app")
                            st.write("- Use manual entry instead")
                        
                        elif result['success']:
                            st.success("✅ Image processed successfully!")
                            
                            # Show extracted text
                            with st.expander("Extracted Text", expanded=False):
                                st.text(result['text'])
                            
                            # Show category and confidence
                            st.write(f"**Detected Category:** {result['category'].title()}")
                            st.write(f"**Confidence:** {result['confidence']:.2f}")
                            
                            # Show amounts found
                            if result['amounts']:
                                st.write("**Amounts Found:**")
                                for amount_info in result['amounts']:
                                    st.write(f"- ${amount_info['amount']:.2f}: {amount_info['description']}")
                            
                            # Show total and suggested calculation
                            if result['total_amount'] > 0:
                                # Use the categorize_expense method for automatic calculation
                                expense_info = calculator.categorize_expense(
                                    result['text'], result['total_amount']
                                )
                                
                                st.write(f"**Total Amount:** ${result['total_amount']:.2f}")
                                st.write(f"**Estimated Carbon Footprint:** {expense_info['carbon_footprint']:.2f} kg CO₂")
                                
                                # Allow user to save
                                if st.button("Save This Entry"):
                                    storage.add_entry(
                                        category=expense_info['category'],
                                        item_type=expense_info['item_type'],
                                        quantity=expense_info['estimated_quantity'],
                                        carbon_footprint=expense_info['carbon_footprint'],
                                        description=f"OCR: {result['text'][:100]}...",
                                        amount_spent=result['total_amount'],
                                        source='ocr',
                                        confidence=result['confidence'],
                                        metadata={
                                            'ocr_text': result['text'],
                                            'amounts_found': result['amounts'],
                                            'specific_data': result['specific_data']
                                        }
                                    )
                                    st.success("✅ Entry saved from OCR data!")
                            
                            # Show suggestions
                            if result['suggestions']:
                                st.write("**AI Suggestions:**")
                                for suggestion in result['suggestions']:
                                    st.info(suggestion)
                        
                        else:
                            st.error(f"❌ {result['error']}")

elif page == "📈 Analytics":
    st.header("Analytics & Trends")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    # Get filtered data
    entries = storage.get_entries(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    if entries:
        df = pd.DataFrame(entries)
        df['date_created'] = pd.to_datetime(df['date_created'])
        df['date'] = df['date_created'].dt.date
        
        # Daily trend
        st.subheader("Daily Carbon Footprint Trend")
        daily_totals = df.groupby('date')['carbon_footprint'].sum().reset_index()
        
        fig = px.line(
            daily_totals, 
            x='date', 
            y='carbon_footprint',
            title="Daily CO₂ Emissions",
            labels={'carbon_footprint': 'CO₂ Emissions (kg)', 'date': 'Date'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Category breakdown over time
        st.subheader("Category Breakdown Over Time")
        category_daily = df.groupby(['date', 'category'])['carbon_footprint'].sum().reset_index()
        
        fig2 = px.bar(
            category_daily,
            x='date',
            y='carbon_footprint',
            color='category',
            title="Daily Emissions by Category",
            labels={'carbon_footprint': 'CO₂ Emissions (kg)', 'date': 'Date'}
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Period Summary")
            total_period = df['carbon_footprint'].sum()
            avg_daily = df.groupby('date')['carbon_footprint'].sum().mean()
            
            st.metric("Total Emissions", f"{total_period:.1f} kg CO₂")
            st.metric("Average Daily", f"{avg_daily:.1f} kg CO₂")
            st.metric("Number of Entries", len(df))
        
        with col2:
            st.subheader("Top Categories")
            category_totals = df.groupby('category')['carbon_footprint'].sum().sort_values(ascending=False)
            
            for category, total in category_totals.head(3).items():
                percentage = (total / total_period) * 100
                st.write(f"**{category.title()}:** {total:.1f} kg ({percentage:.1f}%)")
    
    else:
        st.info("No data available for the selected date range.")

elif page == "🤖 AI Insights & Recommendations":
    st.markdown("## 🤖 AI-Powered Carbon Insights & Recommendations")
    
    # Get user data
    df = storage.get_all_entries_df()
    
    if len(df) < 5:
        st.warning("⚠️ Need at least 5 data entries for AI insights and recommendations.")
        st.info("Current entries: " + str(len(df)))
        st.info("💡 **Get Started:** Add more carbon footprint entries using Manual Entry or Photo Upload to unlock personalized AI insights!")
    else:
        # Main tabs for the merged section
        main_tabs = st.tabs(["🔮 AI Predictions", "🎯 Smart Recommendations", "🧠 Pattern Analysis"])
        
        # Calculate user metrics for all tabs
        daily_avg = df['carbon_footprint'].mean()
        total_emissions = df['carbon_footprint'].sum()
        dominant_category = df.groupby('category')['carbon_footprint'].sum().idxmax()
        
        user_data = {
            'daily_average': daily_avg,
            'total_emissions': total_emissions,
            'dominant_category': dominant_category,
            'entry_count': len(df)
        }
        
        # Get patterns and predictions for all tabs
        patterns = predictive_analytics.analyze_patterns(df)
        predictions = {}
        training_results = {}
        
        if len(df) >= 10:
            with st.spinner("🧠 Training AI models..."):
                training_results = predictive_analytics.train_models(df)
            
            if not any("error" in result for result in training_results.values() if isinstance(result, dict)):
                predictions = predictive_analytics.predict_future_emissions(df, 30)
        
        # Tab 1: AI Predictions
        with main_tabs[0]:
            st.subheader("🔮 Future Emissions Predictions")
            
            if len(df) < 10:
                st.warning("⚠️ Need at least 10 data entries for accurate predictions.")
                st.info("Current entries: " + str(len(df)))
            else:
                if any("error" in result for result in training_results.values() if isinstance(result, dict)):
                    st.error("Failed to train prediction models. Please check your data.")
                else:
                    # Show model performance
                    st.success("✅ AI models trained successfully!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Model Performance:**")
                        model_info = predictive_analytics.get_model_info()
                        
                        # Create a comparison table
                        performance_data = []
                        for model_name, results in training_results.items():
                            if isinstance(results, dict) and 'mae' in results:
                                performance_data.append({
                                    'Model': model_info[model_name]['name'],
                                    'R² Score': f"{results['r2_score']:.3f}",
                                    'MAE': f"{results['mae']:.2f} kg",
                                    'Complexity': model_info[model_name]['complexity']
                                })
                        
                        if performance_data:
                            df_performance = pd.DataFrame(performance_data)
                            st.dataframe(
                                df_performance,
                                column_config={
                                    "Model": st.column_config.TextColumn("Model", width=120),
                                    "R² Score": st.column_config.TextColumn("R²", width=80),
                                    "MAE": st.column_config.TextColumn("MAE", width=100),
                                    "Complexity": st.column_config.TextColumn("Level", width=100)
                                },
                                hide_index=True,
                                use_container_width=True
                            )
            
            with col2:
                st.write("**Model Selection:**")
                trained_models = predictive_analytics.get_trained_models()
                model_names = {
                    'linear': 'Linear Regression',
                    'forest': 'Random Forest', 
                    'gradient_boost': 'Gradient Boosting'
                }
                
                selected_model = st.selectbox(
                    "Choose prediction model:",
                    options=trained_models,
                    format_func=lambda x: model_names.get(x, x),
                    index=0 if trained_models else None
                )
                
                if selected_model:
                    model_details = model_info[selected_model]
                    st.info(f"**{model_details['name']}:** {model_details['description']}")
            
            # Generate predictions
            if st.button("🔮 Generate Predictions", type="primary"):
                if selected_model and predictions:
                    prediction_results = predictive_analytics.predict_with_model(df, selected_model, 30)
                    
                    if 'predictions' in prediction_results:
                        pred_df = prediction_results['predictions']
                        
                        # Create prediction chart
                        fig = px.line(
                            pred_df, 
                            x='date', 
                            y='predicted_emissions',
                            title=f"30-Day Emissions Forecast ({model_names[selected_model]})",
                            color_discrete_sequence=['#1f77b4']
                        )
                        fig.update_layout(
                            height=500,
                            xaxis_title="Date",
                            yaxis_title="Predicted Emissions (kg CO₂)",
                            font=dict(size=12)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Summary metrics
                        st.markdown("**📊 Prediction Summary:**")
                        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                        
                        with metric_col1:
                            st.markdown("""
                            <div class="metric-container">
                                <div class="metric-label">Total (30 days)</div>
                                <div class="metric-value">{:.1f} kg</div>
                            </div>
                            """.format(pred_df['predicted_emissions'].sum()), unsafe_allow_html=True)
                        
                        with metric_col2:
                            st.markdown("""
                            <div class="metric-container">
                                <div class="metric-label">Daily Avg</div>
                                <div class="metric-value">{:.1f} kg</div>
                            </div>
                            """.format(pred_df['predicted_emissions'].mean()), unsafe_allow_html=True)
                        
                        with metric_col3:
                            st.markdown("""
                            <div class="metric-container">
                                <div class="metric-label">Model</div>
                                <div class="metric-value">{}</div>
                            </div>
                            """.format(model_names[selected_model].split()[0]), unsafe_allow_html=True)
                        
                        with metric_col4:
                            confidence = prediction_results.get('confidence', 'N/A')
                            st.markdown("""
                            <div class="metric-container">
                                <div class="metric-label">Confidence</div>
                                <div class="metric-value">{}</div>
                            </div>
                            """.format(confidence if confidence != 'N/A' else 'High'), unsafe_allow_html=True)
                        
                        # Model comparison
                        with st.expander("🔍 Compare All Models"):
                            comparison_data = []
                            for model in trained_models:
                                model_pred = predictive_analytics.predict_with_model(df, model, 30)
                                if 'predictions' in model_pred:
                                    total_pred = model_pred['predictions']['predicted_emissions'].sum()
                                    comparison_data.append({
                                        'Model': model_names[model],
                                        'Total 30-Day Prediction': f"{total_pred:.1f} kg",
                                        'Daily Average': f"{total_pred/30:.1f} kg",
                                        'R² Score': f"{training_results[model]['r2_score']:.3f}"
                                    })
                            
                            if comparison_data:
                                st.dataframe(pd.DataFrame(comparison_data), hide_index=True)
        
        # Tab 2: Smart Recommendations (Based on Predictions)
        with main_tabs[1]:
            st.subheader("🎯 AI-Powered Recommendations")
            
            # Display user profile
            st.write("**👤 Your Carbon Profile:**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Daily Average", f"{daily_avg:.1f} kg CO₂")
            with col2:
                st.metric("vs Global Avg", f"{daily_avg - 36.7:+.1f} kg CO₂")
            with col3:
                st.metric("vs Paris Target", f"{daily_avg - 15.0:+.1f} kg CO₂") 
            with col4:
                sustainability_score = min(100, max(0, (15.0 / daily_avg * 100))) if daily_avg > 0 else 100
                st.metric("Sustainability Score", f"{sustainability_score:.0f}/100")
            
            # Generate prediction-based recommendations
            with st.spinner("🤖 Generating recommendations based on AI predictions..."):
                try:
                    recommendations = smart_recommendations.generate_personalized_recommendations(
                        user_data, patterns, predictions
                    )
                except:
                    # Fallback recommendations based on patterns only
                    recommendations = {
                        'recommendations': {
                            'priority_actions': [
                                {
                                    'action': f'Reduce {dominant_category} emissions',
                                    'category': dominant_category,
                                    'impact': 'High',
                                    'difficulty': 'Medium',
                                    'timeframe': '2-4 weeks',
                                    'estimated_reduction': f'{daily_avg * 0.2:.1f} kg CO₂/day'
                                }
                            ],
                            'quick_wins': [
                                {'action': 'Walk or bike for short trips', 'estimated_reduction': '1-3 kg CO₂/day'},
                                {'action': 'Use energy-efficient appliances', 'estimated_reduction': '0.5-1.5 kg CO₂/day'},
                                {'action': 'Reduce meat consumption', 'estimated_reduction': '2-5 kg CO₂/day'}
                            ]
                        }
                    }
            
            if "error" in str(recommendations):
                st.error(f"Failed to generate recommendations: {recommendations.get('error', 'Unknown error')}")
            else:
                # Prediction-informed recommendations
                if predictions and len(df) >= 10:
                    # Use the most recent prediction or best available model
                    available_models = list(predictions.keys())
                    if available_models:
                        # Prefer gradient_boost, then forest, then linear
                        if 'gradient_boost' in available_models:
                            best_model = 'gradient_boost'
                        elif 'forest' in available_models:
                            best_model = 'forest'
                        else:
                            best_model = available_models[0]
                        
                        pred_data = predictions[best_model]
                        if 'error' not in pred_data:
                            future_avg = pred_data.get('daily_average', daily_avg)
                            model_name = pred_data.get('model_display_name', best_model.title())
                            
                            st.markdown(f"**🤖 AI Prediction Analysis ({model_name}):**")
                            
                            if future_avg > daily_avg:
                                st.warning(f"⚠️ **Alert:** {model_name} predicts your emissions will increase to {future_avg:.1f} kg CO₂/day (+{((future_avg - daily_avg) / daily_avg * 100):+.1f}%)")
                                st.info("💡 **Recommendation:** Focus on the priority actions below to prevent this increase.")
                            elif future_avg < daily_avg:
                                st.success(f"🎉 **Good News:** {model_name} predicts your emissions will decrease to {future_avg:.1f} kg CO₂/day ({((future_avg - daily_avg) / daily_avg * 100):+.1f}%)")
                                st.info("💡 **Keep it up:** Continue your current habits and consider the quick wins below.")
                            else:
                                st.info(f"📊 **Stable Trend:** {model_name} predicts consistent emissions around {future_avg:.1f} kg CO₂/day")
            
            # Priority Actions
            st.subheader("🎯 Priority Actions")
            recs = recommendations.get('recommendations', {})
            
            for i, action in enumerate(recs.get('priority_actions', [])[:3]):
                with st.expander(f"#{i+1} Priority: {action.get('action', 'Unknown action')}", expanded=i==0):
                    col1, col2 = st.columns([3, 2])  # Changed from [2, 1] to [3, 2] for more space
                    
                    with col1:
                        st.write(f"**Category:** {action.get('category', 'Unknown').title()}")
                        st.write(f"**Impact:** {action.get('impact', 'Unknown').title()}")
                        st.write(f"**Difficulty:** {action.get('difficulty', 'Unknown').title()}")
                        st.write(f"**Timeframe:** {action.get('timeframe', 'Unknown')}")
                    
                    with col2:
                        # Use shorter label and add custom styling
                        st.markdown("""
                        <style>
                        .reduction-metric .metric-label {
                            font-size: 0.75rem !important;
                        }
                        .reduction-metric .metric-value {
                            font-size: 1.0rem !important;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        reduction_value = action.get('estimated_reduction', 'Unknown')
                        # Create a more compact display
                        st.markdown(f"""
                        <div class="reduction-metric">
                            <div style="font-size: 0.7rem; color: #666; margin-bottom: 0.2rem;">Potential Reduction</div>
                            <div style="font-size: 1.1rem; font-weight: bold; color: #2e7d32;">{reduction_value}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Progress tracking
                    progress = st.slider(f"Progress on Action #{i+1}", 0, 100, 0, key=f"action_{i}")
                    if progress > 0:
                        st.success(f"Great progress! You're {progress}% complete.")
            
            # Quick Wins
            st.subheader("⚡ Quick Wins")
            quick_wins = recs.get('quick_wins', [])
            
            if quick_wins:
                for i, win in enumerate(quick_wins[:3]):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"• {win.get('action', 'Unknown')}")
                    with col2:
                        st.write(f"**{win.get('estimated_reduction', 'Unknown')}**")
            
            # Prediction-based monthly challenge
            st.subheader("🏆 Monthly Challenge")
            if predictions and len(df) >= 10:
                # Use the most recent prediction or best available model
                available_models = list(predictions.keys())
                if available_models:
                    # Prefer gradient_boost, then forest, then linear
                    if 'gradient_boost' in available_models:
                        best_model = 'gradient_boost'
                    elif 'forest' in available_models:
                        best_model = 'forest'
                    else:
                        best_model = available_models[0]
                    
                    pred_data = predictions[best_model]
                    if 'error' not in pred_data:
                        monthly_predicted = pred_data.get('total_predicted', daily_avg * 30)
                        target_reduction = monthly_predicted * 0.1  # 10% reduction goal
                        
                        st.markdown(f"**AI-Powered Monthly Challenge**")
                        st.write(f"Based on AI predictions, your monthly emissions will be ~{monthly_predicted:.1f} kg CO₂")
                        st.info(f"🎯 **Challenge:** Reduce by {target_reduction:.1f} kg CO₂ this month (10% reduction)")
                        
            challenge_progress = st.slider("Challenge Progress", 0, 100, 0)
            if challenge_progress > 0:
                st.success(f"Challenge Progress: {challenge_progress}%")
            else:
                st.markdown(f"**Monthly Challenge**")
                st.write("Reduce your carbon footprint this month!")
                st.info(f"🎯 **Target:** Reduce daily emissions by 1-2 kg CO₂")
        
        # Tab 3: Pattern Analysis
        with main_tabs[2]:
            st.subheader("🧠 Emission Pattern Analysis")
            
            if "error" not in str(patterns):
                pattern_tabs = st.tabs(["📅 Weekly", "🗓️ Seasonal", "📊 Categories", "📈 Trends"])
                
                with pattern_tabs[0]:
                    if 'weekly_patterns' in patterns:
                        weekly = patterns['weekly_patterns']
                        if 'daily_averages' in weekly:
                            st.write("**Daily Emission Averages:**")
                            for day, avg in weekly['daily_averages'].items():
                                st.write(f"• {day}: {avg:.1f} kg CO₂")
                            
                            st.info(f"💡 **Insight:** Your highest emission day is {weekly.get('highest_day', 'Unknown')}")
                
                with pattern_tabs[1]:
                    if 'seasonal_patterns' in patterns:
                        seasonal = patterns['seasonal_patterns']
                        if 'monthly_averages' in seasonal:
                            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                            monthly_data = seasonal['monthly_averages']['mean']
                            
                            monthly_df = pd.DataFrame({
                                'Month': [months[i-1] for i in monthly_data.keys()],
                                'Average Emissions': list(monthly_data.values())
                            })
                            
                            fig = px.bar(monthly_df, x='Month', y='Average Emissions', 
                                       title="Monthly Emission Patterns")
                            st.plotly_chart(fig, use_container_width=True)
                
                with pattern_tabs[2]:
                    if 'category_patterns' in patterns:
                        cat_patterns = patterns['category_patterns']
                        if 'category_totals' in cat_patterns:
                            cat_df = pd.DataFrame({
                                'Category': list(cat_patterns['category_totals'].keys()),
                                'Total Emissions': list(cat_patterns['category_totals'].values())
                            })
                            
                            fig = px.pie(cat_df, values='Total Emissions', names='Category',
                                       title="Emissions by Category")
                            st.plotly_chart(fig, use_container_width=True)
                
                with pattern_tabs[3]:
                    if 'trend_analysis' in patterns:
                        trend = patterns['trend_analysis']
                        if 'overall_trend' in trend:
                            st.write(f"**Overall Trend:** {trend['overall_trend'].title()}")
                            if trend['overall_trend'] == 'decreasing':
                                st.success("🎉 Great! Your emissions are decreasing over time.")
                            elif trend['overall_trend'] == 'increasing':
                                st.warning("⚠️ Your emissions are increasing. Consider implementing reduction strategies.")
                            else:
                                st.info("📊 Your emissions are relatively stable.")
            else:
                st.error("Unable to analyze patterns. Please ensure you have sufficient data.")

elif page == "🔗 Integrations":
    st.markdown("## 🔗 External Integrations")
    
    st.info("🚀 Connect your apps and devices to automatically track carbon emissions!")
    
    # Integration tabs
    int_tabs = st.tabs(["🏃 Fitness Apps", "🏠 Smart Home", "🌤️ Weather", "📊 Status"])
    
    with int_tabs[0]:  # Fitness Apps
        st.subheader("🏃 Fitness App Integration")
        
        fitness_provider = st.selectbox("Choose fitness app:", 
                                      ["None", "Strava", "Google Fit", "Apple Health"])
        
        if fitness_provider != "None":
            api_key = st.text_input(f"{fitness_provider} API Key:", type="password")
            
            if st.button(f"Connect {fitness_provider}"):
                if api_key:
                    try:
                        fitness_integration = FitnessIntegration(fitness_provider.lower(), api_key)
                        
                        if integration_manager.add_integration(f"fitness_{fitness_provider.lower()}", fitness_integration):
                            st.success(f"✅ Successfully connected to {fitness_provider}!")
                            
                            # Test data sync
                            end_date = datetime.now()
                            start_date = end_date - timedelta(days=7)
                            
                            sync_result = integration_manager.sync_all_integrations(start_date, end_date)
                            
                            if sync_result['total_entries'] > 0:
                                st.info(f"📊 Found {sync_result['total_entries']} transport activities")
                                
                                # Preview data
                                if st.checkbox("Preview data before saving"):
                                    preview_df = pd.DataFrame(sync_result['emissions'])
                                    st.dataframe(preview_df)
                                
                                if st.button("Save fitness data"):
                                    for entry in sync_result['emissions']:
                                        storage.save_entry(
                                            entry['date'],
                                            entry['category'],
                                            entry['description'],
                                            entry['carbon_footprint']
                                        )
                                    st.success("✅ Fitness data saved!")
                            else:
                                st.info("No recent fitness activities found.")
                        else:
                            st.error("❌ Failed to connect. Please check your API key.")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
                else:
                    st.warning("Please enter your API key.")
    
    with int_tabs[1]:  # Smart Home
        st.subheader("🏠 Smart Home Integration")
        
        home_provider = st.selectbox("Choose smart home system:", 
                                   ["None", "Tesla", "Nest", "SmartThings", "Sense"])
        
        if home_provider != "None":
            api_key = st.text_input(f"{home_provider} API Key:", type="password")
            
            if st.button(f"Connect {home_provider}"):
                if api_key:
                    try:
                        home_integration = SmartHomeIntegration(home_provider.lower(), api_key)
                        
                        if integration_manager.add_integration(f"smarthome_{home_provider.lower()}", home_integration):
                            st.success(f"✅ Successfully connected to {home_provider}!")
                            
                            # Demo data
                            st.info("🏠 Smart home integration will automatically track energy usage, heating/cooling, and electric vehicle charging.")
                        else:
                            st.error("❌ Failed to connect. Please check your credentials.")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
                else:
                    st.warning("Please enter your API key.")
    
    with int_tabs[2]:  # Weather
        st.subheader("🌤️ Weather Integration")
        
        weather_key = st.text_input("OpenWeatherMap API Key:", type="password")
        location = st.text_input("Location (city name):", value="New York")
        
        if st.button("Connect Weather Service"):
            if weather_key:
                try:
                    weather_integration = WeatherIntegration(weather_key)
                    
                    if integration_manager.add_integration("weather", weather_integration):
                        st.success("✅ Successfully connected to weather service!")
                        
                        # Test weather data
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=1)
                        
                        weather_data = weather_integration.fetch_data(start_date, end_date, location)
                        
                        if "error" not in weather_data:
                            weather_info = weather_data.get("weather_data", {})
                            temp = weather_info.get("main", {}).get("temp", "N/A")
                            
                            st.info(f"🌡️ Current temperature in {location}: {temp}°C")
                            st.info("🌤️ Weather integration will help analyze heating/cooling emissions based on temperature.")
                        else:
                            st.warning("⚠️ Could not fetch weather data.")
                    else:
                        st.error("❌ Failed to connect. Please check your API key.")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
            else:
                st.warning("Please enter your OpenWeatherMap API key.")
    
    with int_tabs[3]:  # Status
        st.subheader("📊 Integration Status")
        
        available_integrations = integration_manager.get_available_integrations()
        
        if available_integrations:
            status_df = pd.DataFrame(available_integrations)
            st.dataframe(status_df)
            
            if st.button("Sync All Integrations"):
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                
                with st.spinner("Syncing all integrations..."):
                    sync_result = integration_manager.sync_all_integrations(start_date, end_date)
                
                st.success(f"✅ Sync completed! Found {sync_result['total_entries']} new entries.")
                
                if sync_result['total_entries'] > 0:
                    st.json(sync_result['sync_results'])
        else:
            st.info("No integrations connected yet. Set up integrations above to get started!")

elif page == "📍 Location Tracking":
    st.markdown("## 📍 GPS Location Tracking")
    
    st.info("🛰️ Automatically detect transport modes and calculate emissions from your location data.")
    
    # Location tracking tabs
    loc_tabs = st.tabs(["🚗 Add Trip", "⚙️ Settings"])
    
    with loc_tabs[0]:  # Manual Entry
        st.subheader("🚗 Add Trip")
        
        st.info("🗺️ Track your trips by entering start and end locations with transport mode. This automatically calculates distance and carbon emissions!")
        
        # Trip entry form
        with st.form("trip_entry_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📍 Trip Details:**")
                start_location = st.text_input(
                    "Start Location:", 
                    placeholder="e.g., Home, Office, Robson Square"
                )
                end_location = st.text_input(
                    "End Location:", 
                    placeholder="e.g., Airport, Downtown,Stanley Park"
                )
                
                # Transport mode selection
                transport_modes = {
                    'walking': '🚶 Walking',
                    'cycling': '🚴 Cycling',
                    'car_petrol': '🚗 Car (Petrol)',
                    'car_diesel': '🚗 Car (Diesel)', 
                    'car_electric': '🔋 Electric Car',
                    'bus': '🚌 Bus',
                    'train': '🚂 Train',
                    'subway': '🚇 Subway/Metro',
                    'taxi': '🚕 Taxi',
                    'plane_domestic': '✈️ Flight (Domestic)',
                    'plane_international': '✈️ Flight (International)'
                }
                
                transport_mode = st.selectbox(
                    "Transport Mode:",
                    options=list(transport_modes.keys()),
                    format_func=lambda x: transport_modes[x]
                )
        
            with col2:
                st.write("**📅 Trip Timing:**")
                trip_date = st.date_input("Date:", value=datetime.now().date())
                
                # Simple Time Input
                st.write("**🕐 Time:**")
                
                # Time input with text box and radio buttons
                time_col1, time_col2 = st.columns([2, 1])
                
                with time_col1:
                    # Text input for time in HH:MM format
                    current_time = datetime.now()
                    default_time_str = f"{current_time.hour:02d}:{current_time.minute:02d}"
                    
                    time_input = st.text_input(
                        "Enter time (HH:MM):",
                        value=default_time_str,
                        placeholder="09:30",
                        help="Enter time in 24-hour format (e.g., 09:30 for 9:30 AM, 14:30 for 2:30 PM)",
                        label_visibility="collapsed"
                    )
                
                with time_col2:
                    # Radio buttons for AM/PM
                    current_period = "PM" if current_time.hour >= 12 else "AM"
                    time_period = st.radio(
                        "Period:",
                        options=["AM", "PM"],
                        index=1 if current_period == "PM" else 0,
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                
                # Parse and validate time input
                try:
                    if ":" in time_input:
                        hour_str, minute_str = time_input.split(":", 1)
                        input_hour = int(hour_str)
                        input_minute = int(minute_str)
                        
                        # Validate ranges
                        if 0 <= input_hour <= 23 and 0 <= input_minute <= 59:
                            # Convert to 24-hour format if using AM/PM
                            if time_period == "PM" and input_hour != 12:
                                final_hour = input_hour + 12
                            elif time_period == "AM" and input_hour == 12:
                                final_hour = 0
                            else:
                                final_hour = input_hour
                                
                            trip_time = time(final_hour, input_minute)
                            
                            # Show formatted time confirmation
                            st.success(f"⏰ Selected time: {trip_time.strftime('%H:%M')} ({time_input} {time_period})")
                        else:
                            st.error("⚠️ Please enter valid time (Hour: 0-23, Minute: 0-59)")
                            trip_time = time(current_time.hour, current_time.minute)
                    else:
                        st.error("⚠️ Please enter time in HH:MM format")
                        trip_time = time(current_time.hour, current_time.minute)
                        
                except ValueError:
                    st.error("⚠️ Please enter valid numbers for time")
                    trip_time = time(current_time.hour, current_time.minute)
                
                # Optional details
                st.write("**📝 Optional Details:**")
                notes = st.text_area("Notes:", placeholder="Any additional details about the trip")
            
            # Submit button
            submit_trip = st.form_submit_button("🚀 Calculate & Add Trip", type="primary")
        
        if submit_trip:
            if start_location.strip() and end_location.strip():
                with st.spinner("🗺️ Calculating trip distance and emissions..."):
                    # Geocode start and end locations
                    start_coords = location_tracker.geocode_location(start_location)
                    end_coords = location_tracker.geocode_location(end_location)
                    
                    if start_coords and end_coords:
                        # Calculate distance using haversine formula
                        from geopy.distance import geodesic
                        distance_km = geodesic(start_coords, end_coords).kilometers
                        
                        # Calculate carbon footprint
                        emission_factor = location_tracker.emission_factors.get(transport_mode, 0.21)
                        carbon_footprint = distance_km * emission_factor
                        
                        # Calculate final carbon footprint
                        
                        # Display results
                        st.success("✅ Trip calculated successfully!")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Distance", f"{distance_km:.1f} km")
                        with col2:
                            st.metric("Transport", transport_modes[transport_mode])
                        with col3:
                            st.metric("Emissions", f"{carbon_footprint:.2f} kg CO₂")
                        with col4:
                            st.metric("Efficiency", f"{emission_factor:.3f} kg/km")
                        
                        # Automatically save to database
                        st.markdown("---")
                        st.subheader("💾 Saving to Carbon Footprint Database")
                        
                        try:
                            # Save trip to database
                            trip_timestamp = datetime.combine(trip_date, trip_time)
                            
                            st.info("💾 **Saving trip to database...**")
                            entry_id = storage.add_entry(
                                category='transport',
                                item_type=transport_mode,
                                quantity=distance_km,
                                carbon_footprint=carbon_footprint,
                                description=f"Trip from {start_location} to {end_location}. {notes}".strip(),
                                unit='km',
                                source='trip_tracker',
                                metadata={
                                    'start_location': start_location,
                                    'end_location': end_location,
                                    'start_coords': start_coords,
                                    'end_coords': end_coords,
                                    'transport_mode': transport_mode,
                                    'trip_date': trip_timestamp.isoformat(),
                                    'emission_factor': emission_factor
                                }
                            )
                            
                            if entry_id:
                                st.success(f"🎉 **Trip Successfully Saved!** Entry ID: {entry_id}")
                                
                                # Show trip summary
                                st.info(f"""
                                **📊 Trip Summary:**
                                • Route: {start_location} → {end_location}
                                • Distance: {distance_km:.1f} km via {transport_modes[transport_mode]}
                                • Emissions: {carbon_footprint:.2f} kg CO₂
                                • Automatically added to your dashboard statistics!
                                """)
                                
                                # Update session state
                                st.session_state.new_data_added = True
                                st.session_state.last_entry_id = entry_id
                                st.session_state.last_carbon_footprint = carbon_footprint
                                
                                # Verify save
                                try:
                                    verification_entries = storage.get_entries()
                                    latest_entry = None
                                    for entry in verification_entries:
                                        if entry.get('id') == entry_id:
                                            latest_entry = entry
                                            break
                                    
                                    if latest_entry:
                                        st.success("✅ **Database verification successful!** Trip found in database.")
                                    else:
                                        st.error("❌ **Verification failed!** Trip not found in database after save.")
                                        
                                except Exception as verify_error:
                                    st.warning(f"⚠️ Could not verify save: {verify_error}")
                            else:
                                st.error("❌ **Save failed!** No entry ID returned from database.")
                                
                        except Exception as save_error:
                            st.error(f"❌ **Database save error:** {save_error}")
                            st.error(f"**Error details:** {str(save_error)}")
                            
                            # Show database info for debugging
                            import os
                            db_path = storage.db_path
                            if os.path.exists(db_path):
                                db_size = os.path.getsize(db_path)
                                st.info(f"📁 Database file exists: {db_path} ({db_size} bytes)")
                            else:
                                st.error(f"❌ Database file not found: {db_path}")
                        
                        # Show route on map
                        with st.expander("🗺️ View Route on Map", expanded=False):
                            # Create a simple map with start and end points
                            map_data = pd.DataFrame({
                                'lat': [start_coords[0], end_coords[0]],
                                'lon': [start_coords[1], end_coords[1]],
                                'location': [f"Start: {start_location}", f"End: {end_location}"]
                            })
                            st.map(map_data)
                            
                            st.write(f"**Route Details:**")
                            st.write(f"• Start: {start_location} ({start_coords[0]:.4f}, {start_coords[1]:.4f})")
                            st.write(f"• End: {end_location} ({end_coords[0]:.4f}, {end_coords[1]:.4f})")
                            st.write(f"• Distance: {distance_km:.1f} km")
                            st.write(f"• Transport: {transport_modes[transport_mode]}")
                    
                    else:
                        error_locations = []
                        if not start_coords:
                            error_locations.append(f"start location '{start_location}'")
                        if not end_coords:
                            error_locations.append(f"end location '{end_location}'")
                        
                        st.error(f"❌ Could not find coordinates for: {' and '.join(error_locations)}")
                        st.info("💡 Try using more specific addresses (e.g., 'Times Square, New York' instead of just 'Times Square')")
            else:
                st.warning("⚠️ Please enter both start and end locations.")
    
    with loc_tabs[1]:  # Settings
        st.subheader("⚙️ Location Tracking Settings")
        
        # Google Maps API for location context
        st.write("**Google Maps Integration (Optional):**")
        gmaps_key = st.text_input("Google Maps API Key:", type="password")
        
        if gmaps_key:
            if st.button("Test Google Maps API"):
                # Update location tracker with API key
                location_tracker.google_maps_api_key = gmaps_key
                st.success("✅ Google Maps API configured!")
        
        # Export settings
        st.write("**Data Export:**")
        export_days = st.slider("Export last N days:", 1, 90, 30)
        
        if st.button("Export Location Data"):
            end_date = datetime.now()
            start_date = end_date - timedelta(days=export_days)
            
            export_data = location_tracker.export_location_data(start_date, end_date)
            
            st.json(export_data['summary'])
            
            # Download as JSON
            export_json = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                "Download Full Export",
                export_json,
                file_name=f"location_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json",
                mime="application/json"
            )

elif page == "⚙️ Settings":
    st.header("Settings & Data Management")
    
    # Export data
    st.subheader("Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export as CSV"):
            file_path = storage.export_data('csv')
            st.success(f"Data exported to {file_path}")
    
    with col2:
        if st.button("Export as JSON"):
            file_path = storage.export_data('json')
            st.success(f"Data exported to {file_path}")
    
    st.divider()
    
    # Delete data
    st.subheader("Data Management")
    st.warning("⚠️ Danger Zone")
    
    if st.checkbox("I understand this will delete all my data"):
        if st.button("Delete All Data", type="secondary"):
            # This would require implementing a method in DataStorage
            st.error("This feature is not implemented yet for safety reasons.")
    
    st.divider()
    
    # App information
    st.subheader("About")
    st.write("""
    **AI Carbon Footprint Calculator**
    
    This application helps you track and analyze your carbon footprint across different categories:
    - 🚗 **Transport**: Cars, public transport, flights
    - 🍕 **Food**: Meals, groceries, restaurant visits
    - 🏠 **Appliances**: Electricity, heating, cooling
    - 🎬 **Entertainment**: Movies, concerts, streaming
    - 🛍️ **Others**: Shopping, electronics, clothing
    
    **Features:**
    - Natural language processing for easy data entry
    - OCR processing of bills and receipts
    - Real-time analytics and trends
    - Personalized recommendations
    - Data export capabilities
    
    **Carbon Emission Factors:**
    Based on industry-standard emission factors from environmental agencies.
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🌱 Making the world greener, one calculation at a time"
    "</div>",
    unsafe_allow_html=True
) 
