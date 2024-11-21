from typing import List, Dict
import openstack

class ServerManager:
    def __init__(self, config_path: str):
        self.conn = openstack.connect(config_path)

    def create_server(self, name: str, flavor: str, image: str) -> Dict:
        server = self.conn.compute.create_server(name=name, flavor=flavor, image=image)
        return server

    def delete_server(self, server_id: str):
        self.conn.compute.delete_server(server_id)

    def list_active_servers(self) -> List[Dict]:
        return list(self.conn.compute.servers())