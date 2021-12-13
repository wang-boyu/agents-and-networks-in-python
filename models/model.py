from typing import Any

from mesa import Model
from mesa.time import BaseScheduler


class GmuSocial(Model):
    running: bool
    schedule: BaseScheduler
    current_id: int

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def step(self) -> None:
        pass
