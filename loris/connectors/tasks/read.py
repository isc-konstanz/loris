# -*- coding: utf-8 -*-
"""
loris.connectors.tasks.read
~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd
from loris.connectors.tasks.task import ConnectorTask


class ReadTask(ConnectorTask):
    def run(
        self,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None
    ) -> None:
        self._logger.debug(
            f"Reading {len(self.channels)} channels of " f"{type(self.connector).__name__}: " f"{self.connector.uuid}"
        )
        self.connector.read(self.channels, start, end)
