from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Iterable, List, Protocol, runtime_checkable

import attrs
from typeguard import typechecked

from zetta_utils import log

from .task_outcome import TaskOutcome, TaskStatus
from .tasks import Task

logger = log.get_logger("mazepa")


@runtime_checkable
class ExecutionQueue(Protocol):
    name: str

    def push_tasks(self, tasks: Iterable[Task]):
        ...

    def pull_task_outcomes(
        self,
        max_num: int = ...,
    ) -> dict[str, TaskOutcome]:
        ...

    def pull_tasks(self, max_num: int = ...) -> List[Task]:
        ...


@typechecked
@attrs.mutable
class LocalExecutionQueue:
    name: str = "local_execution"
    tasks_todo: list[Task] = attrs.field(init=False, factory=list)
    debug: bool = False
    execution_batch_len: int = 1

    def push_tasks(self, tasks: Iterable[Task]):
        # TODO: Fix progress bar issue with multiple live displays in rich
        # for task in track(tasks, description="Local task execution..."):
        self.tasks_todo += list(tasks)

    def pull_task_outcomes(
        self, max_num: int = 100000, max_time_sec: float = 2.5  # pylint: disable=unused-argument
    ) -> Dict[str, TaskOutcome]:
        task_outcomes: Dict[str, TaskOutcome] = {}

        for task in self.tasks_todo[: self.execution_batch_len]:
            done = False

            while not done:
                task(debug=self.debug)
                assert task.outcome is not None
                task_outcomes[task.id_] = task.outcome

                if task.status != TaskStatus.TRANSIENT_ERROR:
                    if task.outcome.exception is not None:
                        # raise immediatelly for local exec
                        raise task.outcome.exception  # pragma: no cover
                    done = True
                task.curr_retry += 1

        self.tasks_todo = self.tasks_todo[self.execution_batch_len :]
        return task_outcomes

    def pull_tasks(  # pylint: disable=no-self-use
        self, max_num: int = 1  # pylint: disable=unused-argument
    ) -> list[Task]:  # pragma: no cover
        return []


@typechecked
@attrs.frozen
class ExecutionMultiQueue:
    name: str = attrs.field(init=False)
    queues: Iterable[ExecutionQueue]

    def __attrs_post_init__(self):
        name = "_".join(queue.name for queue in self.queues)
        object.__setattr__(self, "name", name)

    def push_tasks(self, tasks: Iterable[Task]):
        tasks_for_queue = defaultdict(list)

        for task in tasks:
            matching_queue_names = [
                queue.name for queue in self.queues if all(tag in queue.name for tag in task.tags)
            ]
            if len(matching_queue_names) == 0:
                raise RuntimeError(
                    f"No queue from set {list(self.queues)} matches " f"all tags {task.tags}."
                )
            tasks_for_queue[matching_queue_names[0]].append(task)

        for queue in self.queues:
            queue.push_tasks(tasks_for_queue[queue.name])

    def pull_task_outcomes(
        self, max_num: int = 500, max_time_sec: float = 2.5
    ) -> Dict[str, TaskOutcome]:
        start_ts = time.time()
        result = {}  # type: dict[str, TaskOutcome]
        for queue in self.queues:
            queue_outcomes = queue.pull_task_outcomes(max_num=max_num - len(result))
            result = {**result, **queue_outcomes}
            if len(result) >= max_num:
                break
            now_ts = time.time()
            if now_ts - start_ts >= max_time_sec:
                break

        return result

    def pull_tasks(self, max_num: int = 1) -> List[Task]:
        result = []  # type: list[Task]

        for queue in self.queues:
            result += queue.pull_tasks(max_num=max_num - len(result))
            if len(result) >= max_num:
                break

        return result
