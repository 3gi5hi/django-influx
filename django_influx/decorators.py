import json
import requests
from . import exceptions
from simplejson import JSONDecodeError


def raise_if_error(func):
    def func_wrapper(*args, **kwargs):
        json_res = {}
        params = kwargs.get('params', {})
        try:
            request = args[0]
            res = func(*args, **kwargs)
            try:
                json_res = res.json()
            except (json.decoder.JSONDecodeError, JSONDecodeError):
                json_res = {}
            res.raise_for_status()

        except requests.exceptions.MissingSchema as err:
            raise exceptions.InfluxDBInvalidURLError(request.base_url)

        except requests.exceptions.ConnectionError as err:
            raise exceptions.InfluxDBConnectionError(err)

        except requests.exceptions.HTTPError as err:
            if json_res and 'error' in json_res and \
                    json_res['error'].startswith('error parsing query:'):
                query = params.get('q')
                error = json_res['error'][len('error parsing query:'):]
                raise exceptions.InfluxDBBadQueryError(query, error)

            if json_res and 'error' in json_res and \
                    json_res['error'].endswith('invalid number'):
                points = kwargs['data']
                raise exceptions.InfluxDBInvalidNumberError(points)

            if json_res and 'error' in json_res and \
                    json_res['error'].endswith('invalid boolean'):
                points = kwargs['data']
                raise exceptions.InfluxDBInvalidBooleanError(points)

            if json_res and 'error' in json_res and \
                    json_res['error'].endswith('bad timestamp'):
                points = kwargs['data']
                raise exceptions.InfluxDBInvalidTimestampError(points)

            if res.status_code == 400:
                query = params.get('q', kwargs.get('data', ''))
                if query == '':
                    raise exceptions.InfluxDBEmptyRequestError(params)
                raise exceptions.InfluxDBBadRequestError(params, json_res.get('error', json_res))
            if res.status_code == 401:
                raise exceptions.InfluxDBUnauthorizedError(err)
            raise err
        return res

    return func_wrapper
