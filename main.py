from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Type, List
from datetime import datetime
from abc import ABC, abstractmethod
from prometheus_client import start_http_server, Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
import openstack

# Prometheus Metrics Definitions
ACTIVE_SERVERS = Gauge('game_servers_active', 'Number of active game servers')
PLAYER_COUNT = Gauge('game_players_current', 'Current number of players')
QUEUE_LENGTH = Gauge('game_queue_length', 'Current queue length')
SCALING_EVENTS = Counter('scaling_events_total', 'Total number of scaling events')
COST_METRIC = Gauge('server_cost_hourly', 'Hourly cost of running servers')

# Configuration Class
class Config:
    def __init__(self):
        self.openstack_config = "/Users/karimshlal/Downloads/clouds.yaml"
        self.password = "DCyaXDfoXDNdOc0kyNPm2hfzsmcjuNITGGnm9iSYMIho5u3ha-ScjoGL6FGw5ODofBOoNsPtGMmQcEN_hJD6dA"
        self.project_id = "338c9c8cfbd246bda6fc7ac29befb8a3"
        self.endpoint_url = "https://pegasus.sky.oslomet.no:5000"

# Abstract Scaling Strategy
class ScalingStrategy(ABC):
    @abstractmethod
    def calculate_scaling_decision(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        pass

# Aggressive Scaling Implementation
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

# Cost-Conscious Scaling Implementation
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

# Cost-Capped Scaling Implementation
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

# Decision Engine
class DecisionEngine:
    def __init__(self, strategies: Dict[str, Type[ScalingStrategy]]):
        self.strategies = strategies

    def decide_scaling_decision(self, strategy_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        strategy = self.strategies[strategy_name]()
        return strategy.calculate_scaling_decision(metrics)

# Server Manager for OpenStack
class ServerManager:
    def __init__(self, username, password, project_id, endpoint_url):
        self.conn = openstack.connect(
            auth_url=endpoint_url,
            project_id=project_id,
            username=username,
            password=password
        )

    def create_server(self, name: str, flavor: str, image: str) -> Dict:
        server = self.conn.compute.create_server(name=name, flavor=flavor, image=image)
        return server

    def delete_server(self, server_id: str):
        self.conn.compute.delete_server(server_id)

    def list_active_servers(self) -> List[Dict]:
        return list(self.conn.compute.servers())

# Visualization for Metrics
class Visualization:
    def update_metrics(self, metrics: Dict[str, Any]):
        ACTIVE_SERVERS.set(metrics['current_servers'])
        PLAYER_COUNT.set(metrics['current_players'])
        QUEUE_LENGTH.set(metrics['queue_length'])
        COST_METRIC.set(metrics.get('daily_cost', 0) / 24)

    def track_scaling_event(self):
        SCALING_EVENTS.inc()

# Initialize App, Configuration, and Components
app = FastAPI()
config = Config()
server_manager = ServerManager(
    username=config.openstack_config,
    password=config.password,
    project_id=config.project_id,
    endpoint_url=config.endpoint_url
)
decision_engine = DecisionEngine({
    'aggressive': AggressiveScaling,
    'cost_conscious': CostConsciousScaling,
    'cost_capped': CostCappedScaling
})
visualization = Visualization()

# Metrics Endpoint for Prometheus
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Scaling Endpoint
@app.post("/scale")
async def trigger_scaling(strategy_name: str):
    # Example metrics; these would usually come from monitoring systems
    metrics = {
        'current_players': 100,
        'server_capacity': 10,
        'current_servers': 1,
        'queue_length': 5,
        'daily_cost': 100.0
    }

    scaling_decision = decision_engine.decide_scaling_decision(strategy_name, metrics)

    if scaling_decision['action'] == 'scale':
        current_servers = scaling_decision['current_servers']
        target_servers = scaling_decision['target_servers']

        # Scale up
        for i in range(current_servers, target_servers):
            server_manager.create_server(f"game-server-{i}", "m1.medium", "game-server-image")

        # Scale down
        active_servers = server_manager.list_active_servers()
        for i in range(target_servers, current_servers):
            server_manager.delete_server(active_servers[i]['id'])

        visualization.track_scaling_event()
        visualization.update_metrics({
            'current_players': metrics['current_players'],
            'current_servers': target_servers,
            'queue_length': metrics['queue_length'],
            'daily_cost': metrics['daily_cost']
        })

    return scaling_decision
