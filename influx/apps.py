from django.apps import AppConfig


class InfluxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'influx'

    # def ready(self):
    #     from .app import Influxable
    #     client = Influxable()
