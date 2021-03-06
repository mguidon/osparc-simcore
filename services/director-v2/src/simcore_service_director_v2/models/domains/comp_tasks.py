from datetime import datetime
from typing import Any, Dict, Optional

from models_library.basic_regex import VERSION_RE
from models_library.projects import ProjectID
from models_library.projects_nodes import Inputs, NodeID, Outputs
from models_library.projects_state import RunningState
from models_library.services import KEY_RE, ServiceInputs, ServiceOutputs
from pydantic import BaseModel, Extra, Field, constr, validator
from pydantic.types import PositiveInt
from simcore_postgres_database.models.comp_tasks import NodeClass, StateType

from ...utils.db import DB_TO_RUNNING_STATE, RUNNING_STATE_TO_DB


class Image(BaseModel):
    name: constr(regex=KEY_RE)
    tag: constr(regex=VERSION_RE)
    requires_gpu: bool
    requires_mpi: bool


class NodeSchema(BaseModel):
    inputs: ServiceInputs = Field(..., description="the inputs scheam")
    outputs: ServiceOutputs = Field(..., description="the outputs schema")

    class Config:
        extra = Extra.forbid
        orm_mode = True


class CompTaskAtDB(BaseModel):
    project_id: ProjectID
    node_id: NodeID
    job_id: Optional[str] = Field(None, description="The celery job ID")
    node_schema: NodeSchema = Field(..., alias="schema")
    inputs: Optional[Inputs] = Field(..., description="the inputs payload")
    outputs: Optional[Outputs] = Field({}, description="the outputs payload")
    run_hash: Optional[str] = Field(
        None,
        description="the hex digest of the resolved inputs +outputs hash at the time when the last outputs were generated",
    )
    image: Image
    submit: datetime
    start: Optional[datetime]
    end: Optional[datetime]
    state: RunningState
    task_id: Optional[PositiveInt]
    internal_id: PositiveInt
    node_class: NodeClass

    @validator("state", pre=True)
    @classmethod
    def convert_state_if_needed(cls, v):
        if isinstance(v, StateType):
            return RunningState(DB_TO_RUNNING_STATE[StateType(v)])
        if isinstance(v, str):
            try:
                state_type = StateType(v)
                return RunningState(DB_TO_RUNNING_STATE[state_type])
            except ValueError:
                pass
        return v

    def to_db_model(self, **exclusion_rules) -> Dict[str, Any]:
        comp_task_dict = self.dict(by_alias=True, exclude_unset=True, **exclusion_rules)
        if "state" in comp_task_dict:
            comp_task_dict["state"] = RUNNING_STATE_TO_DB[comp_task_dict["state"]].value
        return comp_task_dict

    class Config:
        extra = Extra.forbid
        orm_mode = True
