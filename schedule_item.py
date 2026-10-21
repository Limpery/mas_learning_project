from dataclasses import dataclass

from entities.order_entity import OrderEntity
from point import Point


@dataclass
class ScheduleItem:
    order: OrderEntity
    rec_type: str
    start_time: float
    end_time: float
    point_from: Point
    point_to: Point
    cost: float
    all_params: dict
