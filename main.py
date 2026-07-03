"""
Main entry point for TFT Auto Chess system
"""
import cv2
import time
from pathlib import Path

from utils.logger import logger
from config.settings import (
    ENABLE_AUTO_RECOMMENDATION, AUTO_CLICK_ENABLED,
    SCREENSHOT_INTERVAL, DEBUG_MODE
)
from models.card_detector import CardDetector
from models.recommendation_engine import RecommendationEngine
from data.winrate_fetcher import WinrateFetcher


class TFTAutoChess:
    """Main TFT Auto Chess system."""
    
    def __init__(self):
        """Initialize system components."""
        logger.info("Initializing TFT Auto Chess system...")
        
        self.detector = None
        self.recommendation_engine = None
        self.winrate_fetcher = WinrateFetcher()
        
        self.current_cards = []
        self.player_level = 5
        self.gold = 0
        
        self._init_components()
    
    def _init_components(self):
        """Initialize system components."""
        try:
            # Initialize card detector
            logger.info("Loading card detector...")
            self.detector = CardDetector()
            
            # Initialize recommendation engine
            logger.info("Initializing recommendation engine...")
            self.recommendation_engine = RecommendationEngine()
            
            # Load winrate data
            self._load_winrate_data()
            
            logger.info("System initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    def _load_winrate_data(self):
        """Load winrate data from fetcher."""
        try:
            # Fetch data (will use cache if available)
            data = self.winrate_fetcher.fetch_and_cache('tacticians')
            
            if data:
                self.recommendation_engine.load_winrate_data(data)
                logger.info(f"Loaded winrate data for {len(data)} champions")
            else:
                logger.warning("Failed to load winrate data, using default recommendations")
                # Create minimal default data
                default_data = {
                    'ahri': {'win_rate': 0.52, 'pick_rate': 0.05, 'avg_placement': 4.2, 'sample_size': 1000},
                    'akali': {'win_rate': 0.51, 'pick_rate': 0.04, 'avg_placement': 4.3, 'sample_size': 900},
                    'lux': {'win_rate': 0.50, 'pick_rate': 0.03, 'avg_placement': 4.5, 'sample_size': 800},
                }
                self.recommendation_engine.load_winrate_data(default_data)
        
        except Exception as e:
            logger.error(f"Error loading winrate data: {e}")
    
    def process_screenshot(self, image_path: str = None) -> list:
        """
        Process a screenshot and detect cards.
        
        Args:
            image_path: Path to screenshot file. If None, captures from screen.
        
        Returns:
            List of detected cards
        """
        try:
            if image_path and Path(image_path).exists():
                image = cv2.imread(str(image_path))
            else:
                # Would capture from screen in production
                logger.warning("No image path provided, skipping detection")
                return []
            
            if image is None:
                logger.error("Failed to load image")
                return []
            
            # Detect cards
            logger.debug("Detecting cards...")
            detections = self.detector.detect(image)
            
            logger.info(f"Detected {len(detections)} cards")
            for det in detections:
                logger.debug(f"  - {det['name']}: {det['confidence']:.2f}")
            
            return detections
        
        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")
            return []
    
    def get_recommendations(
        self,
        current_cards: list = None,
        level: int = None,
        top_n: int = 5
    ) -> list:
        """
        Get card recommendations.
        
        Args:
            current_cards: List of current champion names
            level: Player level
            top_n: Number of recommendations to return
        
        Returns:
            List of recommended champions with scores
        """
        try:
            cards = current_cards or self.current_cards
            lvl = level or self.player_level
            
            logger.info(f"Getting recommendations for level {lvl} with cards: {cards}")
            
            recommendations = self.recommendation_engine.recommend(
                current_cards=cards,
                level=lvl,
                num_recommendations=top_n
            )
            
            logger.info("Recommendations:")
            for i, (champion, score) in enumerate(recommendations, 1):
                logger.info(f"  {i}. {champion}: {score:.2%}")
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def analyze_synergies(self, current_cards: list = None) -> dict:
        """
        Analyze current synergies.
        
        Args:
            current_cards: List of current champions
        
        Returns:
            Synergy analysis dict
        """
        try:
            cards = current_cards or self.current_cards
            analysis = self.recommendation_engine.get_synergy_analysis(cards)
            
            logger.info("Synergy Analysis:")
            logger.info(f"  Active: {analysis.get('active_synergies', {})}")
            logger.info(f"  Near completion: {analysis.get('near_completion', [])}")
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing synergies: {e}")
            return {}
    
    def run_demo(self):
        """Run demo with example data."""
        logger.info("Starting demo mode...")
        
        # Example current cards
        demo_cards = ['ahri', 'akali']
        demo_level = 5
        
        logger.info(f"Current cards: {demo_cards}")
        logger.info(f"Player level: {demo_level}")
        
        # Get recommendations
        recs = self.get_recommendations(
            current_cards=demo_cards,
            level=demo_level,
            top_n=5
        )
        
        # Analyze synergies
        analysis = self.analyze_synergies(demo_cards)
        
        logger.info("Demo completed")
        
        return {
            'cards': demo_cards,
            'level': demo_level,
            'recommendations': recs,
            'synergies': analysis
        }


def main():
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("TFT Auto Chess System")
    logger.info("=" * 50)
    
    try:
        # Initialize system
        system = TFTAutoChess()
        
        # Run demo
        if DEBUG_MODE:
            result = system.run_demo()
            logger.info(f"Demo result: {result}")
        else:
            logger.info("System initialized and ready")
            logger.info("Use the API to interact with the system")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())