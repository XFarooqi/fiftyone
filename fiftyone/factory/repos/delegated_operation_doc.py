"""
FiftyOne delegated operation repository document.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import logging
from datetime import datetime

from fiftyone.operators import OperatorRegistry
from fiftyone.operators.executor import (
    ExecutionContext,
    ExecutionResult,
    ExecutionRunState,
)

logger = logging.getLogger(__name__)


class DelegatedOperationDocument(object):
    def __init__(
        self,
        operator: str = None,
        delegation_target: str = None,
        context: dict = None,
    ):
        self.operator = operator
        self.operator_label = None
        self.delegation_target = delegation_target
        self.context = (
            context.__dict__
            if isinstance(context, ExecutionContext)
            else context
        )
        self.run_state = (
            ExecutionRunState.QUEUED
        )  # default to queued state on create
        self.queued_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.dataset_id = None
        self.started_at = None
        self.pinned = False
        self.completed_at = None
        self.failed_at = None
        self.result = None
        self.id = None
        self._doc = None

    def from_pymongo(self, doc: dict):
        # required fields
        self.operator = doc["operator"]
        self.queued_at = doc["queued_at"]
        self.run_state = doc["run_state"]
        self.updated_at = doc["updated_at"] if "updated_at" in doc else None

        # optional fields
        self.delegation_target = (
            doc["delegation_target"] if "delegation_target" in doc else None
        )
        self.started_at = doc["started_at"] if "started_at" in doc else None
        self.completed_at = (
            doc["completed_at"] if "completed_at" in doc else None
        )
        self.failed_at = doc["failed_at"] if "failed_at" in doc else None
        self.pinned = doc["pinned"] if "pinned" in doc else None
        self.dataset_id = doc["dataset_id"] if "dataset_id" in doc else None

        if (
            "context" in doc
            and doc["context"] is not None
            and "request_params" in doc["context"]
        ):
            self.context = ExecutionContext(
                request_params=doc["context"]["request_params"],
            )

        if "result" in doc and doc["result"] is not None:

            res = ExecutionResult()
            if "result" in doc["result"]:
                res.result = doc["result"]["result"]
            if "error" in doc["result"]:
                res.error = doc["result"]["error"]

            if res.result or res.error:
                self.result = res

        # internal fields
        self.id = doc["_id"]
        self._doc = doc

        # generated fields:
        try:
            registry = OperatorRegistry()
            if registry.operator_exists(self.operator) is False:
                raise ValueError(
                    "Operator '%s' does not exist" % self.operator
                )

            self.operator_label = registry.get_operator(
                self.operator
            ).config.label
        except Exception as e:
            logger.error("Error getting operator label: %s" % e)

        return self

    def to_pymongo(self) -> dict:
        d = self.__dict__
        d["context"] = (
            d["context"].__dict__
            if isinstance(d["context"], ExecutionContext)
            else d["context"]
        )
        d.pop("_doc")
        d.pop("id")
        return d
