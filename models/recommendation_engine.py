"""
Recommendation engine using winrate data
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from utils.logger import logger
from config.settings import (
    WEIGHT_WINRATE, WEIGHT_SYNERGY, WEIGHT_PLACEMENT,
    TOP_N_RECOMMENDATIONS, MIN_SAMPLE_SIZE
)


class RecommendationEngine:
    """
    Recommendation engine based on winrate data and synergies.
    """
    
    def __init__(self):
        """Initialize recommendation engine."""
        self.winrate_data = {}
        self.synergy_data = {}
        self.placement_data = {}
        self.last_update = None
    
    def load_winrate_data(self, data_source: Dict):
        """
        Load winrate data.
        
        Args:
            data_source: Dict with champion data
                {
                    "champion_name": {
                        "pick_rate": 0.05,
                        "win_rate": 0.52,
                        "avg_placement": 4.2,
                        "sample_size": 1000,
                        "tier": "S"
                    },
                    ...
                }
        """
        self.winrate_data = data_source
        self.last_update = datetime.now()
        logger.info(f"Loaded winrate data for {len(self.winrate_data)} champions")
    
    def load_synergy_data(self, synergies: Dict):
        """
        Load synergy data.
        
        Args:
            synergies: Dict with synergy bonuses
                {
                    "trait_name": {
                        "2": {"stat": "+50% Attack Speed"},
                        "4": {"stat": "+100% Attack Speed"},
                        ...
                    },
                    ...
                }
        """
        self.synergy_data = synergies
        logger.info(f"Loaded synergy data for {len(synergies)} traits")
    
    def load_placement_data(self, placements: Dict):
        """Load placement data for different compositions."""
        self.placement_data = placements
        logger.info("Loaded placement data")
    
    def recommend(
        self,
        current_cards: List[str],
        level: int = 5,
        gold: int = 0,
        num_recommendations: int = TOP_N_RECOMMENDATIONS,
        available_cards: List[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Get card recommendations.
        
        Args:
            current_cards: List of champion names currently owned
            level: Current player level (1-9)
            gold: Current gold available
            num_recommendations: Number of recommendations to return
            available_cards: List of available cards to pick from (None = all)
        
        Returns:
            List of tuples: [(champion_name, score), ...]
            Score is 0-1, higher is better
        """
        if not self.winrate_data:
            logger.warning("No winrate data loaded")
            return []
        
        # Get available cards to recommend
        if available_cards is None:
            available_cards = list(self.winrate_data.keys())
        else:
            available_cards = [c for c in available_cards if c in self.winrate_data]
        
        # Filter cards already owned (optional - enable to avoid duplicates)
        # available_cards = [c for c in available_cards if c not in current_cards]
        
        # Calculate scores
        scores = {}
        for card in available_cards:
            score = self._calculate_score(
                card, current_cards, level, gold
            )
            scores[card] = score
        
        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N
        recommendations = ranked[:num_recommendations]
        logger.debug(f"Generated {len(recommendations)} recommendations")
        
        return recommendations
    
    def _calculate_score(
        self,
        card: str,
        current_cards: List[str],
        level: int,
        gold: int
    ) -> float:
        """
        Calculate recommendation score for a card.
        
        Args:
            card: Champion name
            current_cards: Current owned champions
            level: Player level
            gold: Available gold
        
        Returns:
            Score between 0 and 1
        """
        winrate_score = self._get_winrate_score(card)
        synergy_score = self._get_synergy_score(card, current_cards)
        placement_score = self._get_placement_score(card, current_cards, level)
        
        # Weighted average
        total_score = (
            WEIGHT_WINRATE * winrate_score +
            WEIGHT_SYNERGY * synergy_score +
            WEIGHT_PLACEMENT * placement_score
        )
        
        return total_score
    
    def _get_winrate_score(self, card: str) -> float:
        """
        Get winrate-based score for a card.
        
        Returns: Score 0-1
        """
        if card not in self.winrate_data:
            return 0.0
        
        data = self.winrate_data[card]
        
        # Check sample size
        if data.get('sample_size', 0) < MIN_SAMPLE_SIZE:
            return 0.0
        
        # Normalize winrate (0.4-0.6 range → 0-1 scale)
        win_rate = data.get('win_rate', 0.5)
        score = (win_rate - 0.4) / 0.2  # Maps [0.4-0.6] to [0-1]
        
        return max(0.0, min(1.0, score))
    
    def _get_synergy_score(self, card: str, current_cards: List[str]) -> float:
        """
        Get synergy-based score.
        
        Checks if adding this card completes any synergies or
        increases existing synergy bonuses.
        
        Returns: Score 0-1
        """
        if not self.synergy_data:
            return 0.5  # Neutral if no synergy data
        
        synergy_score = 0.0
        test_team = current_cards + [card]
        
        for trait, bonus_levels in self.synergy_data.items():
            trait_count = sum(
                1 for c in test_team
                if self._has_trait(c, trait)
            )
            
            # Check if this completes a synergy threshold
            for threshold_str, bonus in bonus_levels.items():
                try:
                    threshold = int(threshold_str)
                    if trait_count >= threshold:
                        # Award points based on threshold completion
                        synergy_score += 0.1 / len(self.synergy_data)
                except (ValueError, TypeError):
                    pass
        
        return min(1.0, synergy_score)
    
    def _get_placement_score(
        self,
        card: str,
        current_cards: List[str],
        level: int
    ) -> float:
        """
        Get placement-based score.
        
        Returns: Score 0-1
        """
        if card not in self.winrate_data:
            return 0.0
        
        data = self.winrate_data[card]
        avg_placement = data.get('avg_placement', 4.5)
        
        # Normalize average placement (4-5 range → high score, 8 → low)
        # Lower average placement is better (1=first, 8=last)
        score = (8 - avg_placement) / 4  # Maps [4-8] to [1-0]
        
        return max(0.0, min(1.0, score))
    
    def _has_trait(self, card: str, trait: str) -> bool:
        """Check if card has a specific trait."""
        if card not in self.winrate_data:
            return False
        
        traits = self.winrate_data[card].get('traits', [])
        return trait in traits
    
    def get_synergy_analysis(self, current_cards: List[str]) -> Dict:
        """
        Analyze current synergies.
        
        Args:
            current_cards: List of current champions
        
        Returns:
            Dict with synergy information
        """
        analysis = {
            'active_synergies': {},
            'near_completion': [],
            'recommendations': []
        }
        
        if not self.synergy_data:
            return analysis
        
        for trait, bonuses in self.synergy_data.items():
            trait_count = sum(
                1 for c in current_cards
                if self._has_trait(c, trait)
            )
            
            if trait_count > 0:
                analysis['active_synergies'][trait] = trait_count
                
                # Check for near completion
                for threshold_str in bonuses.keys():
                    try:
                        threshold = int(threshold_str)
                        if 0 < threshold - trait_count <= 2:
                            analysis['near_completion'].append({
                                'trait': trait,
                                'current': trait_count,
                                'next': threshold
                            })
                    except (ValueError, TypeError):
                        pass
        
        return analysis
    
    def get_tier_recommendations(self) -> Dict[str, List[str]]:
        """
        Get champions grouped by tier.
        
        Returns:
            Dict with tiers as keys and champion lists as values
        """
        tiers = {}
        
        for champion, data in self.winrate_data.items():
            tier = data.get('tier', 'UNRANKED')
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(champion)
        
        return tiers


class AdaptiveRecommendationEngine(RecommendationEngine):
    """
    Adaptive recommendation engine that learns from user choices.
    """
    
    def __init__(self):
        """Initialize adaptive engine."""
        super().__init__()
        self.user_preferences = {}
        self.feedback_history = []
    
    def record_feedback(self, recommendation: str, actual_choice: str, outcome: str):
        """
        Record feedback on recommendations.
        
        Args:
            recommendation: Original recommendation
            actual_choice: What user actually picked
            outcome: Result ('good', 'bad', 'neutral')
        """
        feedback = {
            'timestamp': datetime.now(),
            'recommendation': recommendation,
            'actual_choice': actual_choice,
            'outcome': outcome
        }
        self.feedback_history.append(feedback)
        
        logger.debug(f"Recorded feedback: {recommendation} → {actual_choice} ({outcome})")
    
    def update_preferences(self):
        """Update user preferences based on feedback history."""
        if not self.feedback_history:
            return
        
        # Analyze feedback
        recent_feedback = self.feedback_history[-100:]  # Last 100 records
        
        for champion in self.winrate_data.keys():
            good_outcomes = sum(
                1 for f in recent_feedback
                if f['actual_choice'] == champion and f['outcome'] == 'good'
            )
            
            bad_outcomes = sum(
                1 for f in recent_feedback
                if f['actual_choice'] == champion and f['outcome'] == 'bad'
            )
            
            if good_outcomes + bad_outcomes > 0:
                self.user_preferences[champion] = (
                    good_outcomes / (good_outcomes + bad_outcomes)
                )
        
        logger.info(f"Updated preferences for {len(self.user_preferences)} champions")
    
    def recommend_adaptive(
        self,
        current_cards: List[str],
        level: int = 5,
        num_recommendations: int = TOP_N_RECOMMENDATIONS
    ) -> List[Tuple[str, float]]:
        """
        Get adaptive recommendations considering user preferences.
        
        Args:
            current_cards: Current owned champions
            level: Player level
            num_recommendations: Number of recommendations
        
        Returns:
            List of (champion, score) tuples
        """
        base_recommendations = self.recommend(
            current_cards, level, num_recommendations=num_recommendations * 2
        )
        
        # Adjust scores based on user preferences
        adjusted = []
        for champion, base_score in base_recommendations:
            user_pref = self.user_preferences.get(champion, 0.5)
            adjusted_score = base_score * 0.7 + user_pref * 0.3
            adjusted.append((champion, adjusted_score))
        
        # Re-sort and return top N
        adjusted = sorted(adjusted, key=lambda x: x[1], reverse=True)
        return adjusted[:num_recommendations]