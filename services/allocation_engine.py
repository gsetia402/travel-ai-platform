"""
Strategy-based Room Allocation Engine.

Extensible architecture:
- Add new strategies by implementing `AllocationStrategyBase`
- Register them in `STRATEGY_REGISTRY`
- No API changes required
"""

import uuid
import math
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Dict, Tuple

from models.group_trip import TravellerTable
from models.room import RoomTable, RoomAllocationTable, RoomType, ROOM_CAPACITY, AllocationStrategy

logger = logging.getLogger(__name__)


class AllocationStrategyBase(ABC):
    """Base class for room allocation strategies."""

    @abstractmethod
    def group_travellers(self, travellers: List[TravellerTable]) -> Dict[str, List[TravellerTable]]:
        """
        Group travellers into buckets for allocation.
        Returns: dict of group_key -> list of travellers
        """
        pass

    def allocate(
        self,
        trip_id: str,
        travellers: List[TravellerTable],
        room_type: RoomType,
    ) -> Tuple[List[RoomTable], List[RoomAllocationTable]]:
        """Allocate travellers to rooms based on grouping strategy."""
        capacity = ROOM_CAPACITY[room_type]
        groups = self.group_travellers(travellers)

        rooms: List[RoomTable] = []
        allocations: List[RoomAllocationTable] = []
        room_counter = 100

        for group_key, group_travellers in groups.items():
            num_rooms = math.ceil(len(group_travellers) / capacity)

            for i in range(num_rooms):
                room_counter += 1
                room = RoomTable(
                    room_id=str(uuid.uuid4()),
                    trip_id=trip_id,
                    room_number=str(room_counter),
                    room_type=room_type.value,
                    capacity=capacity,
                    gender=group_key if group_key != "ALL" else None,
                )
                rooms.append(room)

                chunk = group_travellers[i * capacity: (i + 1) * capacity]
                for traveller in chunk:
                    alloc = RoomAllocationTable(
                        allocation_id=str(uuid.uuid4()),
                        room_id=room.room_id,
                        traveller_id=traveller.traveller_id,
                    )
                    allocations.append(alloc)

        return rooms, allocations


class SameGenderStrategy(AllocationStrategyBase):
    """Groups travellers by gender. Unknown gender grouped separately."""

    def group_travellers(self, travellers: List[TravellerTable]) -> Dict[str, List[TravellerTable]]:
        groups: Dict[str, List[TravellerTable]] = defaultdict(list)
        for t in travellers:
            gender = (t.gender or "Unknown").strip().capitalize()
            groups[gender].append(t)
        return dict(groups)


class SameDepartmentStrategy(AllocationStrategyBase):
    """Groups travellers by department."""

    def group_travellers(self, travellers: List[TravellerTable]) -> Dict[str, List[TravellerTable]]:
        groups: Dict[str, List[TravellerTable]] = defaultdict(list)
        for t in travellers:
            dept = (t.department or "General").strip()
            groups[dept].append(t)
        return dict(groups)


class SameCityStrategy(AllocationStrategyBase):
    """Groups travellers by city."""

    def group_travellers(self, travellers: List[TravellerTable]) -> Dict[str, List[TravellerTable]]:
        groups: Dict[str, List[TravellerTable]] = defaultdict(list)
        for t in travellers:
            city = (t.city or "Other").strip()
            groups[city].append(t)
        return dict(groups)


class ExecutiveSingleStrategy(AllocationStrategyBase):
    """Allocates each traveller to an individual room (SINGLE override)."""

    def group_travellers(self, travellers: List[TravellerTable]) -> Dict[str, List[TravellerTable]]:
        return {"ALL": travellers}

    def allocate(
        self,
        trip_id: str,
        travellers: List[TravellerTable],
        room_type: RoomType,
    ) -> Tuple[List[RoomTable], List[RoomAllocationTable]]:
        rooms: List[RoomTable] = []
        allocations: List[RoomAllocationTable] = []
        room_counter = 100

        for traveller in travellers:
            room_counter += 1
            room = RoomTable(
                room_id=str(uuid.uuid4()),
                trip_id=trip_id,
                room_number=str(room_counter),
                room_type=RoomType.SINGLE.value,
                capacity=1,
                gender=(traveller.gender or "").strip().capitalize() or None,
            )
            rooms.append(room)
            allocations.append(
                RoomAllocationTable(
                    allocation_id=str(uuid.uuid4()),
                    room_id=room.room_id,
                    traveller_id=traveller.traveller_id,
                )
            )

        return rooms, allocations


# --------------- Strategy Registry ---------------

STRATEGY_REGISTRY: Dict[AllocationStrategy, AllocationStrategyBase] = {
    AllocationStrategy.SAME_GENDER: SameGenderStrategy(),
    AllocationStrategy.SAME_DEPARTMENT: SameDepartmentStrategy(),
    AllocationStrategy.SAME_CITY: SameCityStrategy(),
    AllocationStrategy.EXECUTIVE_SINGLE_ROOM: ExecutiveSingleStrategy(),
}


def get_strategy(strategy: AllocationStrategy) -> AllocationStrategyBase:
    engine = STRATEGY_REGISTRY.get(strategy)
    if not engine:
        raise ValueError(f"Unsupported allocation strategy: {strategy.value}")
    return engine
