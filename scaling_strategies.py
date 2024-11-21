# src/scaling_strategies.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

class ScalingStrategy(ABC):
    @abstractmethod
    def calculate_scaling_decision(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        pass

class AggressiveScaling(ScalingStrategy):
    def calculate_scaling_decision(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        current_players = metrics.get('current_players', 0)
        server_capacity = metrics.get('server_capacity', 100)
        current_servers = metrics.get('current_servers', 1)
        
        needed_servers = max(int((current_players / server_capacity) * 1.2), current_servers + 1)
        
        return {
            'action': 'scale',
            'current_servers': current_servers,
            'target_servers': needed_servers,
            'timestamp': datetime.now().isoformat()
        }

class CostConsciousScaling(ScalingStrategy):
    def calculate_scaling_decision(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        current_players = metrics.get('current_players', 0)
        server_capacity = metrics.get('server_capacity', 100)
        current_servers = metrics.get('current_servers', 1)
        
        needed_servers = max(int((current_players / server_capacity) * 1.05), current_servers)
        
        return {
            'action': 'scale',
            'current_servers': current_servers,
            'target_servers': needed_servers,
            'timestamp': datetime.now().isoformat()
        }

class CostCappedScaling(ScalingStrategy):
    def __init__(self, daily_budget: float):
        self.daily_budget = daily_budget
        self.cost_per_server_hour = 1.0  # Example cost

    def calculate_scaling_decision(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        current_players = metrics.get('current_players', 0)
        server_capacity = metrics.get('server_capacity', 100)
        current_servers = metrics.get('current_servers', 1)
        daily_cost = metrics.get('daily_cost', 0.0)
        
        remaining_budget = self.daily_budget - daily_cost
        max_servers = int(remaining_budget / self.cost_per_server_hour)
        
        needed_servers = min(
            max(int((current_players / server_capacity) * 1.1), current_servers),
            max_servers
        )
        
        return {
            'action': 'scale',
            'current_servers': current_servers,
            'target_servers': needed_servers,
            'timestamp': datetime.now().isoformat(),
            'budget_remaining': remaining_budget
        }