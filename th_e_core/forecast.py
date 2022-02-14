# -*- coding: utf-8 -*-
"""
    th-e-core.forecast
    ~~~~~
    
    This module provides the :class:`pvsyst.Weather`, used as reference to calculate a 
    photovoltaic installations' generated power. The provided environmental data contains 
    temperatures and horizontal solar irradiation, which can be used, to calculate the 
    effective irradiance on defined, tilted photovoltaic systems.
    
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict

import os
import pytz as tz
import datetime as dt
import pandas as pd
import logging

from io import StringIO
from configparser import ConfigParser as Configurations
from th_e_core.configs import Configurable
from th_e_core.iotools import Database
from th_e_core.weather import Weather
from th_e_core.system import System

logger = logging.getLogger(__name__)


class Forecast(ABC, Configurable):

    # noinspection PyShadowingBuiltins
    @classmethod
    def read(cls, system: System, **kwargs) -> Weather:
        configs = cls._read_configs(system, **kwargs)
        type = configs.get('General', 'type', fallback='default')
        if type.lower() in ['default', 'nmm']:
            return NMM(system, configs, **kwargs)

        return cls(system, configs, **kwargs)

    @staticmethod
    def _read_configs(system: System, config_name: str = 'forecast.cfg', **kwargs) -> Configurations:
        return Configurable._read_configs(system.configs.get('General', 'root_dir'),
                                          system.configs.get('General', 'lib_dir'),
                                          system.configs.get('General', 'tmp_dir'),
                                          system.configs.get('General', 'data_dir'),
                                          system.configs.get('General', 'config_dir'),
                                          config_name, **kwargs)

    def __init__(self, system: System, configs: Configurations, **kwargs) -> None:
        Configurable.__init__(self, configs, **kwargs)
        self._system = system
        self._activate(system, configs, **kwargs)

    def _activate(self, system: System, configs: Configurations, **kwargs) -> None:
        pass

    def _rename(self, data: pd.DataFrame, variables: Dict[str, str] = None) -> pd.DataFrame:
        """
        Renames the columns according the variable mapping.

        Parameters
        ----------
        data: DataFrame
        variables: None or dict, default None
            If None, uses self.variables

        Returns
        -------
        data: DataFrame
            Renamed data.
        """
        if variables is None:
            variables = self.variables
        return data.rename(columns={y: x for x, y in variables.items()})

    def get(self,
            start: pd.Timestamp | dt.datetime = dt.datetime.now(),
            end:   pd.Timestamp | dt.datetime = None,
            **kwargs) -> pd.DataFrame:
        """ 
        Retrieves the forecasted data for a specified time interval

        :param start: 
            the start time for which forecasted data will be looked up for.
            For many applications, passing datetime.datetime.now() will suffice.
        :type start: 
            :class:`pandas.Timestamp` or datetime
        
        :param end: 
            the end time for which forecasted data will be looked up for.
            For many applications, passing datetime.datetime.now() will suffice.
        :type end: 
            :class:`pandas.Timestamp` or datetime
        
        :returns: 
            the forecasted data, indexed in a specific time interval.
        
        :rtype: 
            :class:`pandas.DataFrame`
        """
        return self._get_range(self._get(start, end, **kwargs), start, end)

    @abstractmethod
    def _get(self, *args, **kwargs) -> pd.DataFrame:
        pass

    @staticmethod
    def _get_range(forecast: pd.DataFrame,
                   start:    pd.Timestamp | dt.datetime,
                   end:      pd.Timestamp | dt.datetime) -> pd.DataFrame:

        if start is not None:
            start = start.astimezone(forecast.index.tz)
        if start is None or start < forecast.index[0]:
            start = forecast.index[0]

        if end is not None:
            end = end.astimezone(forecast.index.tz)
        if end is None or end > forecast.index[-1]:
            end = forecast.index[-1]

        return forecast.loc[start:end, :]


class DatabaseForecast(Forecast):

    def _activate(self, system: System, configs: Configurations, **kwargs) -> None:
        super()._activate(system, configs, **kwargs)

        data_dir = configs['General']['data_dir']
        if 'dir' in configs['Database']:
            database_dir = configs['Database']['dir']
            if not os.path.isabs(database_dir):
                configs['Database']['dir'] = os.path.join(data_dir, database_dir)
        else:
            configs['Database']['dir'] = data_dir

        self._database = Database.open(self._configs, **kwargs)

    # noinspection PyShadowingBuiltins
    def _get(self,
             start:  pd.Timestamp | dt.datetime = None,
             end:    pd.Timestamp | dt.datetime = None,
             format: str = '%d.%m.%Y',
             **kwargs) -> pd.DataFrame:

        if start is None:
            start = tz.utc.localize(dt.datetime.utcnow())
            start.replace(year=start.year-1, month=1, day=1, hour=0, minute=0, second=0)
        elif isinstance(start, str):
            start = tz.utc.localize(dt.datetime.strptime(start, format))

        if end is None:
            end = start + dt.timedelta(days=364)
        elif isinstance(end, str):
            end = tz.utc.localize(dt.datetime.strptime(end, format))

        return self._database.read(start=start, end=end, **kwargs)


class ScheduledForecast(Forecast):

    def __init__(self, system: System, configs: Configurations, **kwargs) -> None:
        if not configs.has_option('General', 'id'):
            if configs.getboolean('General', 'central', fallback=True):
                if system is None:
                    raise ValueError('Invalid configuration, missing specified forecast id')
                
                configs.set('General', 'id', 
                            '{0:06.2f}'.format(float(system.location.latitude)).replace('.', '') + '_' +
                            '{0:06.2f}'.format(float(system.location.longitude)).replace('.', ''))
        
        self._id = configs.get('General', 'id', fallback='')
        super().__init__(system, configs, **kwargs)

    def _configure(self, configs: Configurations, **kwargs) -> None:
        super()._configure(configs, **kwargs)
        
        self.interval = configs.getint('General', 'interval', fallback=1440)*3600

    def _activate(self, system: System, configs: Configurations, **kwargs) -> None:
        if configs.has_section('Database'):
            if configs.getboolean('General', 'central', fallback=True):
                data_dir = configs['General']['lib_dir']
            else:
                data_dir = configs['General']['data_dir']
            
            if 'dir' in configs['Database']:
                database_dir = configs['Database']['dir']
                if not os.path.isabs(database_dir):
                    configs['Database']['dir'] = os.path.join(data_dir, database_dir)
            else:
                configs['Database']['dir'] = data_dir
            
            self._database = Database.open(configs, **kwargs)
        else:
            self._database = None

    def get(self,
            start: pd.Timestamp | dt.datetime = dt.datetime.now(tz.utc),
            end:   pd.Timestamp | dt.datetime = None,
            **kwargs) -> pd.DataFrame:

        # Calculate the available forecast start and end times
        interval = self.interval/3600
        timezone = tz.timezone(self._system.location.tz)

        if start.tzinfo is None or start.tzinfo.utcoffset(start) is None:
            start = tz.utc.localize(start)

        start_schedule = start.astimezone(timezone).replace(minute=0, second=0, microsecond=0)
        if start_schedule.hour % interval != 0:
            start_schedule = start_schedule - dt.timedelta(hours=start_schedule.hour % interval)

        if self._database is not None and self._database.exists(start_schedule, subdir=self._id):
            forecast = self._database.read(start_schedule, subdir=self._id)

        else:
            forecast = self._get(start, **kwargs)

            if self._database is not None:
                # Store the retrieved forecast
                self._database.write(forecast, start=start_schedule, subdir=self._id)

        return self._get_range(forecast, start, end)

    def _get(self, *args, **kwargs) -> pd.DataFrame:
        # Ignore abstract
        pass


class NMM(ScheduledForecast, Weather):
    """
    Subclass of the Forecast class representing the Meteoblue
    NMM (Nonhydrostatic Meso-Scale Modelling) weather forecast model.
    
    Model data corresponds to 4km resolution forecasts.
    """

    def _configure(self, configs: Configurations, **kwargs) -> None:
        super()._configure(configs, **kwargs)

        # TODO: Add sanity check
        self.name = configs.get('Meteoblue', 'name')
        self.address = configs.get('Meteoblue', 'address')
        self.apikey = configs.get('Meteoblue', 'apikey')

        self.variables = {
            'sunshine':                     'sunshinetime',
            'daylight':                     'isdaylight',
            'temp_air':                     'temperature',
            'temp_felt':                    'felttemperature',
            'wind_speed':                   'windspeed',
            'wind_direction':               'winddirection',
            'humidity_rel':                 'relativehumidity',
            'pressure_sea':                 'sealevelpressure',
            'precipitation_convective':     'convective_precipitation',
            'precipitation_probability':    'precipitation_probability',
            'snow_fraction':                'snowfraction',
            'low_clouds':                   'lowclouds',
            'mid_clouds':                   'midclouds',
            'high_clouds':                  'highclouds',
            'total_clouds':                 'totalcloudcover',
            'uv_index':                     'uvindex',
            'gni':                          'gni_backwards',
            'dni':                          'dni_backwards',
            'ghi':                          'ghi_backwards',
            'dhi':                          'dif_backwards',
            'dhi_instant':                  'dif_instant',
            'etr':                          'extraterrestrialradiation_backwards',
            'etr_instant':                  'extraterrestrialradiation_instant'
        }

        self.variables_output = [
            'sunshine',                     # Sonnenscheindauer [min]
            'daylight',                     # Tageslicht Indikator
            'temp_air',                     # Temperatur [°C]
            'temp_felt',                    # Gefühlte Temperatur [°C]
            'wind_speed',                   # Windgeschwindigkeit [m/s]
            'wind_direction',               # Windrichtung [°]
            'gni',                          # Average Global Normal Irradiance of the last interval [W/m^2]
            'dni',                          # Average Direct Normal Irradiance of the last interval [W/m^2]
            'ghi',                          # Average Global Horizontal Irradiance of the last interval [W/m^2]
            'dhi',                          # Average Diffuse Horizontal Irradiance of the last interval [W/m^2]
            'etr',                          # Average Extraterrestrial Solar Radiation of the last interval [W/m^2]
            'dni_instant',                  # Global Normal Irradiance at the exact time [W/m^2]
            'gni_instant',                  # Global Normal Irradiance at the exact time [W/m^2]
            'ghi_instant',                  # Global Horizontal Irradiance at the exact time [W/m^2]
            'dhi_instant',                  # Diffuse Horizontal Irradiance at the exact time [W/m^2]
            'etr_instant',                  # Extraterrestrial Solar Radiation at the exact time [W/m^2]
            'total_clouds',                 # Gesamtbedeckungsgrad mit Wolken [%]
            'low_clouds',                   # Bedeckungsgrad mit niedrigen Wolken [%]
            'mid_clouds',                   # Bedeckungsgrad mit mittleren Wolken [%]
            'high_clouds',                  # Bedeckungsgrad mit hohen Wolken [%]
            'visibility',                   # Sichtweite [km]
            'uv_index',                     # UV index numbers from 1 to 16
            'humidity_rel',                 # Relative luftfeuchtigkeit [%]
            'pressure_sea',                 # Luftdruck auf Hoehe des Meerespiegels [hPa]
            'precipitation',                # Niederschlagsmenge [mm]
            'precipitation_convective',     # Niederschlag als Schauer [mm]
            'precipitation_probability',    # Niederschlagswahrscheinlichkeit [%]
            'snow_fraction'                 # Schneefall [0.0 - 1.0]
        ]

    def _activate(self, system: System, *args, **kwargs) -> None:
        super()._activate(system, *args, **kwargs)
        from pvlib.location import Location
        if not hasattr(system, 'location') or not isinstance(system.location, Location):
            raise ValueError("Invalid forecast context missing location information")

        self.location = system.location

    # noinspection PyPackageRequirements
    def get_meta(self) -> Dict[str, str]:
        import requests
        import json

        parameters = {
            'name': self.name,
            'tz': self.location.tz,
            'lat': self.location.latitude,
            'lon': self.location.longitude,
            'asl': self.location.altitude,
            'timeformat': 'iso8601',
            'format': 'json',
            'apikey': self.apikey
        }
        response = requests.get(self.address + 'packages/basic-1h_clouds-1h_solar-1h', params=parameters)

        if response.status_code != 200:
            raise requests.HTTPError("Response returned with error " + str(response.status_code) + ": " +
                                     response.reason)

        data = json.loads(response.text)
        return data.get('metadata')

    def _get(self, *_) -> pd.DataFrame:
        data = self._rename(self._get_data())
        return data[self.variables_output]

    # noinspection PyPackageRequirements
    def _get_data(self) -> pd.DataFrame:
        """
        Submits a query to the meteoblue servers and
        converts the CSV response to a pandas DataFrame.
        
        Returns
        -------
        data : DataFrame
            column names are the weather model's variable names.
        """
        import requests

        parameters = {
            'name': self.name,
            'tz': self.location.tz,
            'lat': self.location.latitude,
            'lon': self.location.longitude,
            'asl': self.location.altitude,
            'temperature': 'C',
            'windspeed': 'ms-1',
            'winddirection': 'degree',
            'precipitationamount': 'mm',
            'timeformat': 'iso8601',
            'format': 'csv',
            'apikey': self.apikey
        }
        response = requests.get(self.address + 'packages/basic-1h_clouds-1h_solar-1h', params=parameters)

        if response.status_code != 200:
            raise requests.HTTPError("Response returned with error " + str(response.status_code) + ": " +
                                     response.reason)

        data = pd.read_csv(StringIO(response.text), sep=',')
        data['time'] = pd.to_datetime(data['time'])
        data = data.set_index('time')
        data = data.tz_convert(self.location.tz)
        data = data.replace(-999, 0)

        return data
