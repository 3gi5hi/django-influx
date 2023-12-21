import json
import itertools
import pandas as pd
from .exceptions import InfluxDBInvalidResponseError
from .response import InfluxDBResponse


class BaseSerializer:
    def __init__(self, response, *args, **kwargs):
        if not isinstance(response, InfluxDBResponse):
            msg = '\'response\' must be type of InfluxDBResponse'
            raise InfluxDBInvalidResponseError(msg)
        self.response = response
        self.is_grouped = False
        self.groups = {}

    def convert(self):
        return self.response.raw


class JsonSerializer(BaseSerializer):
    def convert(self):
        return json.dumps(self.response.raw)


class FormattedSerieSerializer(BaseSerializer):
    def convert(self):
        formatted_series = []
        series = self.response.series
        rotation = 0
        for serie in series:
            name = serie.name
            columns = serie.columns
            values = serie.values
            tags = serie.tags
            if tags:
                self.is_grouped = True
                self.groups[rotation] = tags
            if values is None:
                values = [[None] * len(serie.columns)]
            formatted_values = [
                {**dict(zip(columns, v)), **tags, 'tags': tags, 'measurement': serie.name, 'group_id': rotation} for v
                in
                values]
            formatted_series.append({name: formatted_values})
            rotation += 1
        return formatted_series


class FlatFormattedSerieSerializer(FormattedSerieSerializer):
    def convert(self):
        formatted_series = super().convert()
        if len(formatted_series) == 1:
            main_serie = formatted_series[0]
            flat_main_serie = list(main_serie.values())[0]
            return flat_main_serie
        elif len(formatted_series) > 1:
            flat_main_serie = []
            for serie in formatted_series:
                flat_main_serie.extend(list(serie.values())[0])
            return flat_main_serie
        return []


class FlatSimpleResultSerializer(BaseSerializer):
    def convert(self):
        serie = self.response.main_serie
        values = serie.values if serie else []
        flatten_serie = list(itertools.chain(*values))
        return flatten_serie


class FlatSingleValueSerializer(FlatSimpleResultSerializer):
    def convert(self):
        simple_result = super().convert()
        if len(simple_result) == 1:
            return simple_result[0]
        return None


class PandasSerializer(FlatFormattedSerieSerializer):
    def convert(self):
        data = super().convert()
        df = pd.DataFrame(data)
        # df = pd.DataFrame(values, columns=columns)
        return df


class MeasurementPointSerializer(FlatFormattedSerieSerializer):

    def __init__(self, response, measurement):
        from .measurement import MeasurementMeta
        if not isinstance(response, InfluxDBResponse):
            msg = '\'response\' must be type of InfluxDBResponse'
            raise InfluxDBInvalidResponseError(msg)
        if not isinstance(measurement, MeasurementMeta):
            msg = '\'measurement\' must be type of Measurement'
            raise InfluxDBInvalidResponseError(msg)
        super().__init__(response)
        # self.response = response
        self.measurement = measurement

    def convert(self):
        flat_formatted_series = super().convert()
        # timestamp_attributes = self.measurement._get_timestamp_attributes()
        # timestamp_attributes_names = [
        #     ta.attribute_name
        #     for ta in timestamp_attributes
        # ]
        # if 'time' not in timestamp_attributes_names:
        #     timestamp_attributes_names.append('time')
        #
        # self.convert_to_seconds(timestamp_attributes_names, flat_formatted_series)
        return MeasurementQuerySet(flat_formatted_series, self.measurement, self.groups)
        # points = [self.measurement(**ffs) for ffs in flat_formatted_series]
        # return points

    def convert_to_seconds(self, attr_names, series):
        NANO_TO_SEC_RATIO = 1000 * 1000 * 1000
        for field in series:
            for attr_name in attr_names:
                field[attr_name] /= NANO_TO_SEC_RATIO


class MeasurementQuerySet(object):

    def __init__(self, flat_formatted_series, measurement, groups=None):
        self.flat_formatted_series = flat_formatted_series
        self.groups = groups
        self.measurement = measurement
        timestamp_attributes = self.measurement._get_timestamp_attributes()
        timestamp_attributes_names = [
            ta.attribute_name
            for ta in timestamp_attributes
        ]
        if 'time' not in timestamp_attributes_names:
            timestamp_attributes_names.append('time')

        self.convert_to_seconds(timestamp_attributes_names, flat_formatted_series)

    @staticmethod
    def convert_to_seconds(attr_names, series):
        NANO_TO_SEC_RATIO = 1000 * 1000 * 1000
        for field in series:
            for attr_name in attr_names:
                field[attr_name] /= NANO_TO_SEC_RATIO

    def __repr__(self):
        data = list(self[: 20 + 1])
        if len(data) > 20:
            data[-1] = "...(remaining elements truncated)..."
        return "<%s %r>" % (self.__class__.__name__, data)

    def __iter__(self):
        if self.measurement:
            return iter((self.measurement(**ffs) for ffs in self.flat_formatted_series))
        else:
            return iter(pd.DataFrame(self.flat_formatted_series))

    def __getitem__(self, k):
        if isinstance(k, slice):
            if self.measurement:
                return (self.measurement(**ffs) for ffs in self.flat_formatted_series[k])
            else:
                df = pd.DataFrame(self.flat_formatted_series[k])
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df
        else:
            if self.measurement:
                return self.measurement(**self.flat_formatted_series[k])
            else:
                df = pd.DataFrame(self.flat_formatted_series[k])
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df

    def dataframe(self):
        df = pd.DataFrame(self.flat_formatted_series)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def points(self):
        return (self.measurement(**ffs) for ffs in self.flat_formatted_series)

    def json(self):
        return self.flat_formatted_series

    def tagged_groups(self):
        def generate_group(series):
            if self.measurement:
                return (self.measurement(**ffs) for ffs in series)
            else:
                df = pd.DataFrame(series)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df

        return (
            (group, generate_group([ffs for ffs in self.flat_formatted_series if ffs['group_id'] == group_id])) for
            group_id, group in self.groups.items()
        )
