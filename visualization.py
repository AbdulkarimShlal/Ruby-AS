import prometheus_client
from prometheus_client import start_http_server, Gauge, Counter

ACTIVE_SERVERS = Gauge('game_servers_active', 'Number of active game servers')
PLAYER_COUNT = Gauge('game_players_current', 'Current number of players')
QUEUE_LENGTH = Gauge('game_queue_length', 'Current queue length')
SCALING_EVENTS = Counter('scaling_events_total', 'Total number of scaling events')
COST_METRIC = Gauge('server_cost_hourly', 'Hourly cost of running servers')

class Visualization:
    def __init__(self):
        start_http_server(8000)

    def update_metrics(self, metrics: Dict[str, Any]):
        ACTIVE_SERVERS.set(metrics['current_servers'])
        PLAYER_COUNT.set(metrics['current_players'])
        QUEUE_LENGTH.set(metrics['queue_length'])
        COST_METRIC.set(metrics['daily_cost'] / 24)

    def track_scaling_event(self):
        SCALING_EVENTS.inc()