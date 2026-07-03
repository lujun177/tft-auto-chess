"""
Winrate data fetcher from various sources
"""
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

from utils.logger import logger
from config.settings import CACHE_DIR, WINRATE_UPDATE_FREQUENCY


class WinrateFetcher:
    """
    Fetch and cache winrate data from multiple sources.
    """
    
    # Popular TFT winrate data sources
    SOURCES = {
        'tacticians': {
            'url': 'https://tacticians.gg/api/data/current-set',
            'parser': 'parse_tacticians'
        },
        'tftactics': {
            'url': 'https://tftactics.gg/api/meta',
            'parser': 'parse_tftactics'
        }
    }
    
    def __init__(self, cache_dir: Path = CACHE_DIR):
        """
        Initialize winrate fetcher.
        
        Args:
            cache_dir: Directory to cache winrate data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = 10  # seconds
    
    def fetch_and_cache(self, source: str = 'tacticians', force_refresh: bool = False) -> Optional[Dict]:
        """
        Fetch winrate data and cache it.
        
        Args:
            source: Data source ('tacticians' or 'tftactics')
            force_refresh: Force fetch even if cached data is fresh
        
        Returns:
            Dict with winrate data or None if failed
        """
        # Check cache first
        cache_file = self.cache_dir / f"{source}_winrate.json"
        
        if not force_refresh and cache_file.exists():
            # Check if cache is still fresh
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_age < timedelta(hours=WINRATE_UPDATE_FREQUENCY):
                logger.info(f"Loading cached data from {source}")
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load cache: {e}")
        
        # Fetch fresh data
        logger.info(f"Fetching fresh winrate data from {source}...")
        data = self._fetch_from_source(source)
        
        if data:
            # Cache the data
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"Cached data to {cache_file}")
            except Exception as e:
                logger.warning(f"Failed to cache data: {e}")
        
        return data
    
    def _fetch_from_source(self, source: str) -> Optional[Dict]:
        """Fetch data from a specific source."""
        if source not in self.SOURCES:
            logger.error(f"Unknown source: {source}")
            return None
        
        try:
            source_info = self.SOURCES[source]
            url = source_info['url']
            parser = source_info['parser']
            
            logger.debug(f"Fetching from {url}...")
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse response
            raw_data = response.json()
            parsed_data = getattr(self, parser)(raw_data)
            
            logger.info(f"Successfully fetched data from {source}")
            return parsed_data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from {source}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing data from {source}: {e}")
            return None
    
    @staticmethod
    def parse_tacticians(data: Dict) -> Dict:
        """
        Parse data from Tacticians.gg API.
        
        Returns standardized format:
        {
            "champion_name": {
                "pick_rate": float,
                "win_rate": float,
                "avg_placement": float,
                "sample_size": int,
                "tier": str,
                "traits": [list of traits]
            }
        }
        """
        parsed = {}
        
        try:
            # Structure might vary, adjust based on actual API response
            champions = data.get('units', [])
            
            for champ in champions:
                name = champ.get('name', '').lower()
                if not name:
                    continue
                
                parsed[name] = {
                    'pick_rate': champ.get('pickRate', 0.0) / 100.0,
                    'win_rate': champ.get('winRate', 0.5) / 100.0,
                    'avg_placement': champ.get('avgPlacement', 4.5),
                    'sample_size': champ.get('games', 0),
                    'tier': champ.get('tier', 'UNRANKED'),
                    'traits': champ.get('traits', []),
                    'cost': champ.get('cost', 1)
                }
        
        except Exception as e:
            logger.error(f"Error parsing Tacticians data: {e}")
        
        return parsed
    
    @staticmethod
    def parse_tftactics(data: Dict) -> Dict:
        """
        Parse data from TFTactics API.
        """
        parsed = {}
        
        try:
            # Adjust based on actual API response
            if 'champions' in data:
                champions = data['champions']
            else:
                champions = data.get('units', [])
            
            for champ in champions:
                name = champ.get('name', '').lower()
                if not name:
                    continue
                
                parsed[name] = {
                    'pick_rate': champ.get('pickRate', 0.0) / 100.0,
                    'win_rate': champ.get('winRate', 0.5) / 100.0,
                    'avg_placement': champ.get('avgPlacement', 4.5),
                    'sample_size': champ.get('matches', 0),
                    'tier': champ.get('tier', 'UNRANKED'),
                    'traits': champ.get('classes', []) + champ.get('origins', []),
                    'cost': champ.get('cost', 1)
                }
        
        except Exception as e:
            logger.error(f"Error parsing TFTactics data: {e}")
        
        return parsed
    
    def get_cached_data(self, source: str = 'tacticians') -> Optional[Dict]:
        """Get cached data without fetching."""
        cache_file = self.cache_dir / f"{source}_winrate.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read cache: {e}")
        
        return None
    
    def clear_cache(self, source: Optional[str] = None):
        """Clear cache for a source or all sources."""
        if source:
            cache_file = self.cache_dir / f"{source}_winrate.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cleared cache for {source}")
        else:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Cleared all caches")


class SynergyDataFetcher:
    """Fetch synergy information."""
    
    @staticmethod
    def get_example_synergies() -> Dict:
        """
        Get example synergy data for demonstration.
        
        Real data should be fetched from official sources.
        """
        return {
            'assassin': {
                '2': {'effect': 'Assassins leap to the enemy backline'},
                '4': {'effect': 'Assassins deal 75% more damage on their first attack'},
                '6': {'effect': 'Assassins deal 100% more damage on their first attack'}
            },
            'knight': {
                '2': {'effect': 'Gain 15% damage reduction'},
                '4': {'effect': 'Gain 30% damage reduction'},
                '6': {'effect': 'Gain 40% damage reduction'}
            },
            'mage': {
                '2': {'effect': 'Spell power +20%'},
                '4': {'effect': 'Spell power +50%'},
                '6': {'effect': 'Spell power +80%'}
            },
            # Add more traits as needed
        }


# Example usage
if __name__ == "__main__":
    fetcher = WinrateFetcher()
    
    # Fetch from primary source
    data = fetcher.fetch_and_cache('tacticians')
    
    if data:
        print(f"Fetched data for {len(data)} champions")
        for name, stats in list(data.items())[:3]:
            print(f"  {name}: WR={stats['win_rate']:.1%}, PR={stats['pick_rate']:.1%}")
    else:
        print("Failed to fetch data")