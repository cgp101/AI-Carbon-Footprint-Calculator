"""
Smart Recommendations Engine
Uses Azure OpenAI to provide personalized carbon reduction suggestions
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from config import get_azure_openai_config

class SmartRecommendations:
    def __init__(self):
        self.azure_config = get_azure_openai_config()
        self.recommendation_cache = {}
        
    def generate_personalized_recommendations(self, user_data: Dict, patterns: Dict, predictions: Dict) -> Dict:
        """Generate personalized recommendations using Azure OpenAI"""
        try:
            # Prepare context for AI
            context = self._prepare_ai_context(user_data, patterns, predictions)
            
            # Generate recommendations using Azure OpenAI
            recommendations = self._call_azure_openai_for_recommendations(context)
            
            # Structure and enhance recommendations
            structured_recommendations = self._structure_recommendations(recommendations, user_data)
            
            return structured_recommendations
            
        except Exception as e:
            return {"error": f"Failed to generate recommendations: {str(e)}"}
    
    def _prepare_ai_context(self, user_data: Dict, patterns: Dict, predictions: Dict) -> str:
        """Prepare context data for AI analysis"""
        
        # Calculate key metrics
        total_emissions = user_data.get('total_emissions', 0)
        daily_average = user_data.get('daily_average', 0)
        dominant_category = patterns.get('category_patterns', {}).get('dominant_category', 'unknown')
        trend = patterns.get('trend_analysis', {}).get('overall_trend', 'unknown')
        
        # Global context
        global_average = 36.7  # kg CO2 per day (world average)
        paris_target = 15.0   # kg CO2 per day (Paris Agreement target)
        
        context = f"""
        User Carbon Footprint Analysis:
        
        Current Performance:
        - Daily average emissions: {daily_average:.1f} kg CO2
        - Total tracked emissions: {total_emissions:.1f} kg CO2
        - Dominant emission category: {dominant_category}
        - Emission trend: {trend}
        - Performance vs global average ({global_average} kg CO2/day): {'Above' if daily_average > global_average else 'Below'}
        - Performance vs Paris target ({paris_target} kg CO2/day): {'Above' if daily_average > paris_target else 'Below'}
        
        Pattern Analysis:
        {json.dumps(patterns, indent=2)}
        
        Future Predictions:
        {json.dumps(predictions, indent=2)}
        
        Please provide personalized, actionable recommendations to reduce carbon emissions based on this analysis.
        Focus on the areas with highest impact and provide specific, measurable actions.
        """
        
        return context
    
    def _call_azure_openai_for_recommendations(self, context: str) -> Dict:
        """Call Azure OpenAI API to generate recommendations"""
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.azure_config["api_key"]
        }
        
        prompt = f"""
        You are an expert environmental consultant specializing in carbon footprint reduction.
        Based on the user's carbon footprint data and patterns, provide specific, actionable recommendations.
        
        {context}
        
        Please provide recommendations in the following JSON format:
        {{
            "priority_actions": [
                {{
                    "action": "specific action to take",
                    "category": "transport/food/appliances/entertainment/other",
                    "impact": "high/medium/low",
                    "estimated_reduction": "X.X kg CO2 per day",
                    "difficulty": "easy/medium/hard",
                    "timeframe": "immediate/1-week/1-month/3-months"
                }}
            ],
            "quick_wins": [
                {{
                    "action": "easy immediate action",
                    "estimated_reduction": "X.X kg CO2 per day"
                }}
            ],
            "long_term_goals": [
                {{
                    "goal": "major lifestyle change",
                    "estimated_reduction": "X.X kg CO2 per day",
                    "investment_required": "none/low/medium/high"
                }}
            ],
            "personalized_insights": [
                "insight about user's specific patterns",
                "another personalized observation"
            ],
            "monthly_challenge": {{
                "title": "30-day challenge title",
                "description": "detailed challenge description",
                "target_reduction": "X.X kg CO2"
            }}
        }}
        
        Make recommendations specific to the user's data and focus on their dominant emission categories.
        """
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert environmental consultant. Always respond with valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                self.azure_config["chat_endpoint"],
                headers=headers,
                json=payload,
                params={"api-version": self.azure_config["api_version"]}
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                
                # Clean and parse JSON response
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                
                return json.loads(content)
            else:
                return {"error": f"API call failed: {response.status_code}"}
                
        except Exception as e:
            # Fallback recommendations if API fails
            return self._get_fallback_recommendations(context)
    
    def _structure_recommendations(self, ai_recommendations: Dict, user_data: Dict) -> Dict:
        """Structure and enhance AI recommendations with additional data"""
        
        if "error" in ai_recommendations:
            return ai_recommendations
        
        # Add additional metadata and structure
        structured = {
            "generated_at": datetime.now().isoformat(),
            "user_profile": {
                "daily_average": user_data.get('daily_average', 0),
                "dominant_category": user_data.get('dominant_category', 'unknown'),
                "improvement_potential": self._calculate_improvement_potential(user_data)
            },
            "recommendations": ai_recommendations,
            "implementation_tracker": self._create_implementation_tracker(ai_recommendations),
            "progress_metrics": self._define_progress_metrics(ai_recommendations)
        }
        
        return structured
    
    def _calculate_improvement_potential(self, user_data: Dict) -> Dict:
        """Calculate potential for improvement"""
        daily_avg = user_data.get('daily_average', 0)
        global_avg = 36.7
        paris_target = 15.0
        
        potential = {
            "current_vs_global": {
                "difference": daily_avg - global_avg,
                "percentage": ((daily_avg - global_avg) / global_avg * 100) if global_avg > 0 else 0
            },
            "current_vs_paris": {
                "difference": daily_avg - paris_target,
                "percentage": ((daily_avg - paris_target) / paris_target * 100) if paris_target > 0 else 0
            },
            "improvement_potential": max(0, daily_avg - paris_target),
            "sustainability_score": min(100, max(0, (paris_target / daily_avg * 100))) if daily_avg > 0 else 100
        }
        
        return potential
    
    def _create_implementation_tracker(self, recommendations: Dict) -> Dict:
        """Create tracker for recommendation implementation"""
        tracker = {
            "priority_actions": [],
            "quick_wins": [],
            "long_term_goals": [],
            "monthly_challenge": {}
        }
        
        # Initialize tracking for each recommendation type
        for action in recommendations.get("priority_actions", []):
            tracker["priority_actions"].append({
                "action": action.get("action", ""),
                "status": "not_started",
                "progress": 0,
                "start_date": None,
                "target_date": None,
                "notes": ""
            })
        
        for win in recommendations.get("quick_wins", []):
            tracker["quick_wins"].append({
                "action": win.get("action", ""),
                "status": "not_started",
                "completed_date": None
            })
        
        for goal in recommendations.get("long_term_goals", []):
            tracker["long_term_goals"].append({
                "goal": goal.get("goal", ""),
                "status": "not_started",
                "progress": 0,
                "milestones": [],
                "target_completion": None
            })
        
        challenge = recommendations.get("monthly_challenge", {})
        if challenge:
            tracker["monthly_challenge"] = {
                "title": challenge.get("title", ""),
                "status": "not_started",
                "progress": 0,
                "start_date": None,
                "daily_targets": []
            }
        
        return tracker
    
    def _define_progress_metrics(self, recommendations: Dict) -> Dict:
        """Define metrics to track progress"""
        
        # Calculate total potential reduction
        total_potential = 0
        
        for action in recommendations.get("priority_actions", []):
            reduction_str = action.get("estimated_reduction", "0 kg CO2 per day")
            reduction = self._extract_reduction_value(reduction_str)
            total_potential += reduction
        
        for win in recommendations.get("quick_wins", []):
            reduction_str = win.get("estimated_reduction", "0 kg CO2 per day")
            reduction = self._extract_reduction_value(reduction_str)
            total_potential += reduction
        
        metrics = {
            "total_potential_reduction": total_potential,
            "target_milestones": [
                {"percentage": 25, "reduction": total_potential * 0.25, "timeframe": "1 month"},
                {"percentage": 50, "reduction": total_potential * 0.50, "timeframe": "3 months"},
                {"percentage": 75, "reduction": total_potential * 0.75, "timeframe": "6 months"},
                {"percentage": 100, "reduction": total_potential, "timeframe": "1 year"}
            ],
            "success_indicators": [
                "Daily emissions below previous 30-day average",
                "Completion of 3+ quick wins",
                "Active progress on 2+ priority actions",
                "Monthly challenge participation"
            ]
        }
        
        return metrics
    
    def _extract_reduction_value(self, reduction_str: str) -> float:
        """Extract numerical value from reduction string"""
        try:
            import re
            match = re.search(r'(\d+\.?\d*)', reduction_str)
            return float(match.group(1)) if match else 0.0
        except:
            return 0.0
    
    def _get_fallback_recommendations(self, context: str) -> Dict:
        """Provide fallback recommendations if AI fails"""
        return {
            "priority_actions": [
                {
                    "action": "Switch to public transportation or bike for short trips",
                    "category": "transport",
                    "impact": "high",
                    "estimated_reduction": "5.0 kg CO2 per day",
                    "difficulty": "medium",
                    "timeframe": "immediate"
                },
                {
                    "action": "Reduce meat consumption to 2-3 times per week",
                    "category": "food",
                    "impact": "high",
                    "estimated_reduction": "3.0 kg CO2 per day",
                    "difficulty": "medium",
                    "timeframe": "1-week"
                },
                {
                    "action": "Optimize home heating/cooling by 2-3 degrees",
                    "category": "appliances",
                    "impact": "medium",
                    "estimated_reduction": "2.0 kg CO2 per day",
                    "difficulty": "easy",
                    "timeframe": "immediate"
                }
            ],
            "quick_wins": [
                {
                    "action": "Unplug electronics when not in use",
                    "estimated_reduction": "0.5 kg CO2 per day"
                },
                {
                    "action": "Take shorter showers (5 minutes instead of 10)",
                    "estimated_reduction": "0.8 kg CO2 per day"
                },
                {
                    "action": "Switch to LED light bulbs",
                    "estimated_reduction": "0.3 kg CO2 per day"
                }
            ],
            "long_term_goals": [
                {
                    "goal": "Install solar panels or switch to renewable energy",
                    "estimated_reduction": "8.0 kg CO2 per day",
                    "investment_required": "high"
                },
                {
                    "goal": "Transition to electric or hybrid vehicle",
                    "estimated_reduction": "6.0 kg CO2 per day",
                    "investment_required": "high"
                }
            ],
            "personalized_insights": [
                "Your carbon footprint analysis suggests room for improvement in multiple categories",
                "Focus on the largest emission sources for maximum impact"
            ],
            "monthly_challenge": {
                "title": "30-Day Carbon Reduction Challenge",
                "description": "Implement one quick win and one priority action for 30 days",
                "target_reduction": "3.0 kg CO2"
            }
        }
    
    def get_weekly_tips(self, user_patterns: Dict) -> List[Dict]:
        """Generate weekly tips based on user patterns"""
        tips = []
        
        # Analyze patterns and generate contextual tips
        if user_patterns.get('weekly_patterns', {}).get('highest_day'):
            highest_day = user_patterns['weekly_patterns']['highest_day']
            tips.append({
                "title": f"Optimize Your {highest_day}",
                "description": f"Your highest emission day is {highest_day}. Consider planning lower-impact activities on this day.",
                "category": "pattern-based",
                "difficulty": "easy"
            })
        
        if user_patterns.get('seasonal_patterns', {}).get('highest_month'):
            highest_month = user_patterns['seasonal_patterns']['highest_month']
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_name = month_names[highest_month - 1] if 1 <= highest_month <= 12 else 'Unknown'
            tips.append({
                "title": f"Prepare for {month_name} Emissions",
                "description": f"Your emissions tend to be higher in {month_name}. Plan energy-efficient strategies for this period.",
                "category": "seasonal",
                "difficulty": "medium"
            })
        
        # Add general weekly tips
        general_tips = [
            {
                "title": "Meatless Monday",
                "description": "Start the week with plant-based meals to reduce food emissions",
                "category": "food",
                "difficulty": "easy"
            },
            {
                "title": "Walk Wednesday",
                "description": "Choose walking or cycling for mid-week errands",
                "category": "transport", 
                "difficulty": "easy"
            },
            {
                "title": "Energy Efficient Friday",
                "description": "Review and optimize your energy usage before the weekend",
                "category": "appliances",
                "difficulty": "easy"
            }
        ]
        
        tips.extend(general_tips)
        return tips[:5]  # Return top 5 tips
    
    def update_recommendation_progress(self, recommendation_id: str, progress_data: Dict) -> Dict:
        """Update progress on a specific recommendation"""
        # This would typically update a database
        # For now, return the updated progress structure
        return {
            "recommendation_id": recommendation_id,
            "updated_at": datetime.now().isoformat(),
            "progress": progress_data,
            "next_steps": self._generate_next_steps(progress_data)
        }
    
    def _generate_next_steps(self, progress_data: Dict) -> List[str]:
        """Generate next steps based on current progress"""
        progress = progress_data.get('progress', 0)
        
        if progress < 25:
            return [
                "Set up daily reminders for your chosen action",
                "Track your baseline measurements",
                "Identify potential obstacles and solutions"
            ]
        elif progress < 50:
            return [
                "Review and adjust your approach if needed",
                "Celebrate your progress so far",
                "Consider adding a complementary action"
            ]
        elif progress < 75:
            return [
                "Document what's working well",
                "Share your success with others",
                "Plan for long-term sustainability"
            ]
        else:
            return [
                "Prepare to maintain this new habit",
                "Consider taking on a new challenge",
                "Help others implement similar changes"
            ] 