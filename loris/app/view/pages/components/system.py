# -*- coding: utf-8 -*-
"""
loris.app.view.pages.components.system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import dash_bootstrap_components as dbc

from loris import System
from loris.app.view.pages import PageLayout, register_component_page
from loris.app.view.pages.components import ComponentGroup, ComponentPage


@register_component_page(System)
class SystemPage(ComponentGroup, ComponentPage[System]):
    def __init__(self, system: System, *args, **kwargs) -> None:
        super().__init__(component=system, *args, **kwargs)

    @property
    def path(self) -> str:
        return f"/{self._component.TYPE}/{self._encode_id(self._component.key)}"

    def _create_data_layout(self, layout: PageLayout, **_) -> None:
        if len(self.data.channels) > 0:
            layout.append(
                dbc.Row(
                    dbc.Col(
                        dbc.Card(dbc.CardBody(self._build_data())),
                    ),
                ),
            )

    def _do_create_layout(self) -> PageLayout:
        for page in self:
            page._do_create_layout()
        return super()._do_create_layout()

    def _do_register(self) -> None:
        super()._do_register()
        for page in self:
            page._do_register()