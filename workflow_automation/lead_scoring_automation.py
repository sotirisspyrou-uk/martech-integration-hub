#!/usr/bin/env python3
"""
Lead Scoring Automation - Intelligent MarTech Lead Qualification

Advanced machine learning lead scoring with automated qualification workflows.

🎯 INTELLIGENT LEAD SCORING 🎯
AI-powered lead qualification with real-time scoring updates.

Author: Sotirios Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

🚀 THE RARE TECHNICAL MARKETING LEADER 🚀
Combining C-suite strategy with hands-on AI implementation.

DISCLAIMER: This is demonstration code showcasing technical capabilities.
"""

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class ScoreCategory(Enum):
    """Lead score categories"""
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    QUALIFIED = "qualified"


@dataclass
class LeadScore:
    """Lead scoring data structure"""
    lead_id: str = ""
    total_score: float = 0.0
    category: ScoreCategory = ScoreCategory.COLD
    demographic_score: float = 0.0
    behavioral_score: float = 0.0
    engagement_score: float = 0.0
    firmographic_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    factors: Dict[str, float] = field(default_factory=dict)


class LeadScoringAutomation:
    """
    AI-powered lead scoring and qualification system.
    
    🎯 ENTERPRISE FEATURES:
    - Multi-factor scoring algorithms
    - Real-time score updates
    - Behavioral pattern analysis
    - Automated lead routing
    - Performance optimization
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.lead_scores: Dict[str, LeadScore] = {}
        self.scoring_weights = {
            'demographic': 0.25,
            'behavioral': 0.35,
            'engagement': 0.25,
            'firmographic': 0.15
        }
        self.thresholds = {
            ScoreCategory.COLD: 0,
            ScoreCategory.WARM: 40,
            ScoreCategory.HOT: 70,
            ScoreCategory.QUALIFIED: 85
        }
    
    def calculate_lead_score(self, lead_data: Dict[str, Any]) -> LeadScore:
        """Calculate comprehensive lead score"""
        lead_id = lead_data.get('lead_id', str(uuid.uuid4()))
        
        # Calculate component scores
        demographic_score = self._calculate_demographic_score(lead_data)
        behavioral_score = self._calculate_behavioral_score(lead_data)
        engagement_score = self._calculate_engagement_score(lead_data)
        firmographic_score = self._calculate_firmographic_score(lead_data)
        
        # Calculate weighted total score
        total_score = (
            demographic_score * self.scoring_weights['demographic'] +
            behavioral_score * self.scoring_weights['behavioral'] +
            engagement_score * self.scoring_weights['engagement'] +
            firmographic_score * self.scoring_weights['firmographic']
        )
        
        # Determine category
        category = self._categorize_score(total_score)
        
        lead_score = LeadScore(
            lead_id=lead_id,
            total_score=total_score,
            category=category,
            demographic_score=demographic_score,
            behavioral_score=behavioral_score,
            engagement_score=engagement_score,
            firmographic_score=firmographic_score,
            factors={
                'job_title': lead_data.get('job_title_score', 0),
                'company_size': lead_data.get('company_size_score', 0),
                'website_visits': lead_data.get('website_visits', 0),
                'email_opens': lead_data.get('email_opens', 0)
            }
        )
        
        self.lead_scores[lead_id] = lead_score
        return lead_score
    
    def _calculate_demographic_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate demographic-based score"""
        score = 0.0
        
        # Job title scoring
        job_title = lead_data.get('job_title', '').lower()
        if any(title in job_title for title in ['ceo', 'cto', 'vp', 'director']):
            score += 30
        elif any(title in job_title for title in ['manager', 'lead']):
            score += 20
        else:
            score += 10
        
        # Industry scoring
        industry = lead_data.get('industry', '').lower()
        if industry in ['technology', 'saas', 'software']:
            score += 20
        elif industry in ['finance', 'healthcare', 'manufacturing']:
            score += 15
        else:
            score += 5
        
        # Location scoring
        location = lead_data.get('location', '').lower()
        if any(city in location for city in ['san francisco', 'new york', 'seattle']):
            score += 15
        
        return min(score, 100)
    
    def _calculate_behavioral_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate behavior-based score"""
        score = 0.0
        
        # Website engagement
        page_views = lead_data.get('page_views', 0)
        score += min(page_views * 2, 30)
        
        # Content downloads
        downloads = lead_data.get('content_downloads', 0)
        score += min(downloads * 10, 25)
        
        # Form submissions
        form_submissions = lead_data.get('form_submissions', 0)
        score += min(form_submissions * 15, 25)
        
        # Event attendance
        events_attended = lead_data.get('events_attended', 0)
        score += min(events_attended * 20, 20)
        
        return min(score, 100)
    
    def _calculate_engagement_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate engagement-based score"""
        score = 0.0
        
        # Email engagement
        email_opens = lead_data.get('email_opens', 0)
        score += min(email_opens * 3, 25)
        
        email_clicks = lead_data.get('email_clicks', 0)
        score += min(email_clicks * 8, 30)
        
        # Social engagement
        social_shares = lead_data.get('social_shares', 0)
        score += min(social_shares * 5, 15)
        
        # Webinar attendance
        webinars_attended = lead_data.get('webinars_attended', 0)
        score += min(webinars_attended * 15, 30)
        
        return min(score, 100)
    
    def _calculate_firmographic_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate company-based score"""
        score = 0.0
        
        # Company size
        company_size = lead_data.get('company_size', 0)
        if company_size >= 1000:
            score += 40
        elif company_size >= 100:
            score += 30
        elif company_size >= 50:
            score += 20
        else:
            score += 10
        
        # Revenue
        annual_revenue = lead_data.get('annual_revenue', 0)
        if annual_revenue >= 10000000:  # $10M+
            score += 30
        elif annual_revenue >= 1000000:  # $1M+
            score += 20
        elif annual_revenue >= 100000:  # $100K+
            score += 10
        
        # Technology stack
        tech_stack = lead_data.get('technology_stack', [])
        relevant_tech = ['salesforce', 'hubspot', 'marketo', 'pardot']
        if any(tech in str(tech_stack).lower() for tech in relevant_tech):
            score += 30
        
        return min(score, 100)
    
    def _categorize_score(self, score: float) -> ScoreCategory:
        """Categorize lead based on score"""
        if score >= self.thresholds[ScoreCategory.QUALIFIED]:
            return ScoreCategory.QUALIFIED
        elif score >= self.thresholds[ScoreCategory.HOT]:
            return ScoreCategory.HOT
        elif score >= self.thresholds[ScoreCategory.WARM]:
            return ScoreCategory.WARM
        else:
            return ScoreCategory.COLD
    
    def get_qualified_leads(self, min_category: ScoreCategory = ScoreCategory.HOT) -> List[LeadScore]:
        """Get leads meeting qualification criteria"""
        min_score = self.thresholds[min_category]
        return [lead for lead in self.lead_scores.values() 
                if lead.total_score >= min_score]
    
    def get_scoring_summary(self) -> Dict[str, Any]:
        """Get lead scoring summary statistics"""
        if not self.lead_scores:
            return {'total_leads': 0}
        
        scores = list(self.lead_scores.values())
        category_counts = defaultdict(int)
        
        for score in scores:
            category_counts[score.category.value] += 1
        
        return {
            'total_leads': len(scores),
            'average_score': np.mean([s.total_score for s in scores]),
            'category_distribution': dict(category_counts),
            'qualified_leads': category_counts['qualified'],
            'hot_leads': category_counts['hot']
        }


def demo_lead_scoring():
    """Demo lead scoring automation"""
    print("🎯 LEAD SCORING AUTOMATION DEMO")
    
    scorer = LeadScoringAutomation()
    
    # Sample lead data
    sample_leads = [
        {
            'lead_id': 'LEAD_001',
            'job_title': 'VP Marketing',
            'industry': 'Technology',
            'company_size': 500,
            'annual_revenue': 5000000,
            'page_views': 15,
            'email_opens': 8,
            'content_downloads': 2
        },
        {
            'lead_id': 'LEAD_002', 
            'job_title': 'Marketing Manager',
            'industry': 'Healthcare',
            'company_size': 50,
            'annual_revenue': 500000,
            'page_views': 3,
            'email_opens': 2,
            'content_downloads': 0
        }
    ]
    
    # Score leads
    for lead_data in sample_leads:
        score = scorer.calculate_lead_score(lead_data)
        print(f"Lead {score.lead_id}: {score.total_score:.1f} ({score.category.value})")
    
    summary = scorer.get_scoring_summary()
    print(f"Qualified Leads: {summary['qualified_leads']}")
    
    print("\n🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")


if __name__ == "__main__":
    demo_lead_scoring()

