"""Print the Pydantic JSON Schemas for committing through apply_patch."""

import json

from pydantic import TypeAdapter

from server.schemas import (
    Area, Brief, ErrorResponse, Meta, Overlap, ProjectCollection,
    ProjectFeature, SearchResult,
)
from server.storm.schemas import StormEstimate


MODELS = {
    "project": ProjectFeature,
    "projects": ProjectCollection,
    "overlap": Overlap,
    "brief": Brief,
    "area": Area,
    "meta": Meta,
    "search-result": SearchResult,
    "error": ErrorResponse,
    "storm-estimate": StormEstimate,
}


def exported_schemas() -> dict[str, dict]:
    return {
        name: {"$schema": "https://json-schema.org/draft/2020-12/schema", **TypeAdapter(model).json_schema()}
        for name, model in MODELS.items()
    }


if __name__ == "__main__":
    print(json.dumps(exported_schemas(), ensure_ascii=False, sort_keys=True, indent=2))
