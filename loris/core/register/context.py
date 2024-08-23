# -*- coding: utf-8 -*-
"""
loris.core.register.context
~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import itertools
import os
import re
from abc import abstractmethod
from collections import OrderedDict
from copy import deepcopy
from typing import Callable, Collection, Iterator, Optional, Type, TypeVar, get_args

from loris.core import Configurations, Context, Directories, ResourceException
from loris.core.register import Registrator, Registry

R = TypeVar("R", bound=Registrator)


class RegistratorContext(Context[R]):
    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def SECTION(self) -> str:
        pass

    def __init__(self, context: Context, *args, **kwargs) -> None:
        from loris.data.context import DataContext
        if context is None or not isinstance(context, DataContext):
            raise ResourceException(f"Invalid data context: {None if context is None else type(context)}")
        super().__init__(context, *args, **kwargs)
        self.__map = OrderedDict[str, R]()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({[c.id for c in self.__map.values()]})"

    def __str__(self) -> str:
        return f"{type(self).__name__}:\n\t" + "\n\t".join([f"{i} = {repr(c)}" for i, c in self.__map.items()])

    def __iter__(self) -> Iterator[str]:
        return iter(self.__map)

    def __len__(self) -> int:
        return len(self.__map)

    def __contains__(self, __value: str | R) -> bool:
        if isinstance(__value, str):
            return __value in self.__map.keys()
        if isinstance(__value, self._get_type()):
            return __value in self.values()
        return False

    def __getitem__(self, __uid: str) -> R:
        return self._get(__uid)

    def __setitem__(self, __uid: str, __value: R) -> None:
        self._set(__uid, __value)

    def __delitem__(self, __uid: str) -> None:
        del self.__map[__uid]

    @property
    @abstractmethod
    def _registry(self) -> Registry[R]:
        pass

    # noinspection PyProtectedMember, PyUnresolvedReferences
    def _load_sections(
        self,
        context: RegistratorContext | Registrator,
        configs: Configurations,
        defaults: Optional[Mapping[str, Any]] = None,
    ) -> Collection[R]:
        values = []
        _type = self._get_type()
        if defaults is None:
            defaults = {}

        for section in _type.SECTIONS:
            if section in configs:
                defaults.update(configs.get(section))
        for section_name in configs.sections:
            if section_name in _type.SECTIONS:
                continue
            section_file = f"{section_name}.conf"
            section_default = deepcopy(defaults)
            section_default.update(configs.get(section_name))
            section = Configurations.load(
                section_file,
                **configs.dirs.encode(),
                **section_default,
                require=False
            )
            values.append(self._update(context, section))
        return values

    # noinspection PyProtectedMember, PyTypeChecker, PyUnresolvedReferences
    @staticmethod
    def _load_from_file(
        context: RegistratorContext,
        configs_dirs: Directories,
        configs_file: str,
        defaults: Mapping[str, Any],
    ) -> Collection[R]:
        values = []
        if configs_dirs.conf.joinpath(configs_file).is_file():
            configs = Configurations(configs_file, deepcopy(configs_dirs))
            configs._load()
            values.extend(context._load_sections(context, configs, defaults))
        return values

    # noinspection PyTypeChecker, PyProtectedMember, PyUnresolvedReferences
    def _load_from_dir(
        self,
        context: RegistratorContext | Registrator,
        configs_dir: str,
        defaults: Mapping[str, Any],
    ) -> Collection[R]:
        values = []
        if os.path.isdir(configs_dir):
            config_types = tuple(itertools.chain(*[[t.type, *t.alias] for t in self._registry.types.values()]))
            for configs_entry in os.scandir(configs_dir):
                if (configs_entry.is_file() and configs_entry.path.endswith('.conf')
                        and not configs_entry.path.endswith('default.conf')
                        and configs_entry.name.startswith(config_types)):

                    configs_dirs = self.configs.dirs.encode()
                    configs_dirs["conf_dir"] = os.path.dirname(configs_entry.path)
                    configs = Configurations.load(
                        configs_entry.name,
                        **configs_dirs,
                        **defaults
                    )
                    values.append(self._update(context, configs))
        return values

    def _sort(self):
        def convert(text: str) -> int | str:
            return int(text) if text.isdigit() else text

        self.__map = OrderedDict(
            sorted(self.__map.items(), key=lambda e: [convert(t) for t in re.split("([0-9]+)", e[0])])
        )

    # noinspection PyShadowingBuiltins
    def filter(self, filter: Callable[[R], bool]) -> Collection[R]:
        return [c for c in self.__map.values() if filter(c)]

    # noinspection PyUnresolvedReferences
    def _get_type(self) -> Type[R]:
        return get_args(self._registry.__orig_class__)[0]

    # noinspection PyMethodMayBeStatic
    def get_types(self) -> Collection[str]:
        return self._registry.types.keys()

    def has_type(self, *types: str | type) -> bool:
        if len(types) == 0:
            raise ValueError("At least one type to look up required")
        return len(self.get_all(*types)) > 0

    def get_all(self, *types: Optional[str | type]) -> Collection[R]:
        if len(types) > 0:
            return [
                value for value in self.__map.values()
                if (
                    any(t.startswith(value.TYPE) for t in types if isinstance(t, str))
                    or any(isinstance(value, t) for t in types if isinstance(t, type))
                )
            ]
        else:
            return self.__map.values()

    def get_first(self, *types: Optional[str | type]) -> Optional[R]:
        return next(iter(self.get_all(*types)))

    # noinspection PyTypeChecker
    def get_last(self, *types: Optional[str | type]) -> Optional[R]:
        return next(reversed(self.get_all(*types)))

    def _get(self, __uid: str) -> R:
        return self.__map[__uid]

    def _set(self, __uid: str, __value: R) -> None:
        self.__map[__uid] = __value

    def _add(self, *__values: R) -> None:
        for __value in __values:
            self._set(__value.id, __value)

    # noinspection PyProtectedMember, SpellCheckingInspection
    def _new(self, context: Context, configs: Configurations) -> R:
        registrator_type = self._get_type()
        registration_name = "_".join(os.path.splitext(configs.name)[:-1])
        if registrator_type.SECTION not in configs.sections:
            configs._add_section(registrator_type.SECTION, {"key": registration_name})
        registrator_section = configs[registrator_type.SECTION]
        if "key" not in configs[registrator_type.SECTION]:
            registrator_section["key"] = registration_name
            registrator_section.move_to_top("key")

        registration_type = re.split(r"[^a-zA-Z0-9\s]", registration_name)[0]
        if "type" in registrator_section:
            registration_type = registrator_section.get("type").lower()
        elif "type" in configs:
            _registration_type = configs.get("type").lower()
            if self._registry.has_type(_registration_type):
                registration_type = _registration_type
        if not self._registry.has_type(registration_type):
            raise ResourceException(f"Invalid registration type: {registration_type}")

        for registration in self._registry.types.values():
            if registration.is_alias(registration_type):
                registration_type = registration.type
                self._logger.debug(
                    f"Using alias \"{','.join(registration.alias)}\" " f"for registration: {registration_type}"
                )
        if "type" not in registrator_section:
            registrator_section["type"] = registration_type
        return self._registry.types[registration_type].initialize(context, configs)

    def _update(self, context: Context, configs: Configurations) -> R:
        value = self._new(context, configs)
        if value.id in self:
            self._get(value.id).configs.update(configs)
        else:
            self._add(value)
        return value
