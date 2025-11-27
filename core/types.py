from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

class ArtifactType(Enum):
    STEP_FILE = "STEP_FILE"
    BREP_FILE = "BREP_FILE"
    STL_FILE = "STL_FILE"
    MSH_FILE = "MSH_FILE"
    VALIDATION_REPORT = "VALIDATION_REPORT"

@dataclass
class Artifact:
    type: ArtifactType
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"Artifact({self.type.name}, path='{self.path}')"

class AgentStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

@dataclass
class AgentResult:
    status: AgentStatus
    artifact: Optional[Artifact] = None
    log: str = ""
    error: Optional[str] = None
