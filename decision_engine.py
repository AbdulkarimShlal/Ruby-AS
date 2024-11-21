from typing import Dict, Type
from .scaling_strategies import ScalingStrategy, AggressiveScaling, CostConsciousScaling, CostCappedScaling

class DecisionEngine:
    def __init__(self, strategies: Dict[str, Type[ScalingStrategy]]):
        self.strategies = strategies

    def decide_scaling_action(self, strategy_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        strategy = self.strategies[strategy_name]()
        return strategy.calculate_scaling_decision(metrics)