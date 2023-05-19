from __future__ import annotations

import dataclasses
import dataclasses_json

@dataclasses_json.dataclass_json
@dataclasses.dataclass
class Route:
    source: str
    destination: str

    def return_route(self) -> Route:
        return Route(self.destination, self.source)