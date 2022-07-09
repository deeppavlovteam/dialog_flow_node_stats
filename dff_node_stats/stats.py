"""
Stats
**********
| Defines the Stats class that is used to collect information on each turn of the :py:class:`~df_engine.core.actor.Actor` .
| An instance of the :py:class:`~df_engine.core.actor.Actor` class should be passed to the update_actor_handlers method in order to register a callback.

Example::

    stats = Stats()

    actor = Actor()

    stats.update_actor_handlers(actor, auto_save=False)

"""
from typing import Any, Dict, List, Optional
import datetime
from functools import cached_property
from copy import copy

import pandas as pd
from pydantic import validate_arguments
from df_engine.core import Context, Actor
from df_engine.core.types import ActorStage

from . import collectors as DSC
from .savers import Saver


class Stats:
    """
    The class which is used to collect information from :py:class:`~df_engine.core.context.Context`
    on each turn of the :py:class:`~df_engine.core.actor.Actor`.

    Parameters
    ----------

    saver: :py:class:`~dff_node_stats.savers.Saver`
        An instance of the Saver class that is used to save the collected data in the desired storage.
    collectors: Optional[List[:py:class:`~dff_node_stats.collectors.Collector`]]
        Instances of the :py:class:`~dff_node_stats.collectors.Collector` class.
        Their method :py:meth:`~dff_node_stats.collectors.Collector.collect_stats`
        is invoked each turn of the :py:class:`~df_engine.core.actor.Actor` to save the desired information.

    """

    def __init__(
        self,
        saver: Saver,
        collectors: Optional[List[DSC.Collector]] = None,
    ) -> None:
        col_default = [DSC.DefaultCollector()]
        collectors = col_default if collectors is None else col_default + collectors
        type_check = lambda x: isinstance(x, DSC.Collector) and not isinstance(x, type)
        if not all(map(type_check, collectors)):
            raise TypeError("Param `collectors` should be a list of collector instances")
        column_dtypes = dict()
        parse_dates = list()
        for collector in collectors:
            column_dtypes.update(collector.column_dtypes)
            parse_dates.extend(collector.parse_dates)

        self.saver: Saver = saver
        self.collectors: List[DSC.Collector] = collectors
        self.column_dtypes: Dict[str, str] = column_dtypes
        self.parse_dates: List[str] = parse_dates
        self.dfs: list = []
        self.start_time: Optional[datetime.datetime] = None

    def __deepcopy__(self, *args, **kwargs):
        return copy(self)

    @cached_property
    def dataframe(self) -> pd.DataFrame:
        return self.saver.load(column_types=self.column_dtypes, parse_dates=self.parse_dates)

    def add_df(self, stats: Dict[str, Any]) -> None:
        self.dfs += [pd.DataFrame(stats)]

    def save(self, *args, **kwargs):
        self.saver.save(self.dfs, column_types=self.column_dtypes, parse_dates=self.parse_dates)
        self.dfs.clear()

    @validate_arguments
    def _update_handlers(self, actor: Actor, stage: ActorStage, handler) -> Actor:
        actor.handlers[stage] = actor.handlers.get(stage, []) + [handler]
        return actor

    def update_actor_handlers(self, actor: Actor, auto_save: bool = True, *args, **kwargs):
        actor = self._update_handlers(actor, ActorStage.CONTEXT_INIT, self.get_start_time)
        actor = self._update_handlers(actor, ActorStage.FINISH_TURN, self.collect_stats)
        if auto_save:
            actor = self._update_handlers(actor, ActorStage.FINISH_TURN, self.save)

    @validate_arguments
    def get_start_time(self, ctx: Context, actor: Actor, *args, **kwargs) -> None:
        self.start_time = datetime.datetime.now()
        self.collect_stats(ctx, actor, *args, **kwargs)

    @validate_arguments
    def collect_stats(self, ctx: Context, actor: Actor, *args, **kwargs) -> None:
        stats = dict()
        for collector in self.collectors:
            stats.update(collector.collect_stats(ctx, actor, start_time=self.start_time))
        self.add_df(stats=stats)
