from influxdb import InfluxDBClient


class DatabaseHandler:

    def __init__(self, host, port, username, password):
        self.client = InfluxDBClient(host=host, port=port, username=username, password=password)
        self.client.create_database('IoT')
        self.client.switch_database('IoT')
        self.json_body = None

    def close(self):
        self.client.close()

    def prepare_data(self, data):
        self.json_body = data

    def insert_data(self):
        self.client.write_points(self.json_body)

