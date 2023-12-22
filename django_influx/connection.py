from django.conf import settings
from .api import InfluxDBApi
from .request import InfluxDBRequest


class Connection:
    def __init__(self, *args, **kwargs):
        self.influx_host = kwargs.get('host', settings.INFLUXDB['HOST'])
        self.user = kwargs.get('user', settings.INFLUXDB['USER'])
        self.password = kwargs.get('password', settings.INFLUXDB['PASSWORD'])
        self.database_name = kwargs.get('database_name', settings.INFLUXDB['NAME'])
        options = settings.INFLUXDB['OPTIONS']
        self.base_url = kwargs.get(
            'base_url',
            f'{"https://" if eval(options.get("ssl", "False")) else "http://"}{self.influx_host}:{settings.INFLUXDB["PORT"]}'
        )

        self.auth = (self.user, self.password)
        self.request = InfluxDBRequest(
            self.base_url,
            self.database_name,
            auth=self.auth,
        )
        self.stream = False
        self.check_if_connection_reached()

    @staticmethod
    def create(base_url, database_name, user='', password=''):
        return Connection(base_url, database_name, user, password)

    def check_if_connection_reached(self):
        query = 'SHOW DATABASES'
        InfluxDBApi.execute_query(self.request, query)

    @property
    def policy_name(self):
        return 'autogen'

    @property
    def full_database_name(self):
        return '"{}"."{}"'.format(self.database_name, self.policy_name)