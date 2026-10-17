from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from .world import GridWorld, Position


@dataclass(order=True)
class QueueItem:
    priority: int
    position: Position = field(compare=False)


class NoSafePath(RuntimeError):
    pass


def a_star(world: GridWorld, start: Position, goal: Position) -> list[Position]:
    """Return the lowest-energy path, using distance as an admissible heuristic."""
    frontier = [QueueItem(0, start)]
    came_from: dict[Position, Position | None] = {start: None}
    cost_so_far = {start: 0}

    while frontier:
        current = heapq.heappop(frontier).position
        if current == goal:
            break
        for neighbor in world.neighbors(current):
            candidate_cost = cost_so_far[current] + world.energy_cost(neighbor)
            if candidate_cost < cost_so_far.get(neighbor, 10**9):
                cost_so_far[neighbor] = candidate_cost
                priority = candidate_cost + neighbor.manhattan(goal)
                heapq.heappush(frontier, QueueItem(priority, neighbor))
                came_from[neighbor] = current

    if goal not in came_from:
        raise NoSafePath(f"No traversable path from {start} to {goal}")

    path = []
    cursor: Position | None = goal
    while cursor is not None:
        path.append(cursor)
        cursor = came_from[cursor]
    return list(reversed(path))
