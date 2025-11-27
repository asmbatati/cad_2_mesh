import os
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.BRepTools import breptools_Write
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SHELL

from core.types import Artifact, ArtifactType, AgentResult, AgentStatus

class ParserAgent:
    def __init__(self, name="Parser"):
        self.name = name

    def run(self, input_artifact: Artifact, output_dir: str) -> AgentResult:
        if input_artifact.type != ArtifactType.STEP_FILE:
            return AgentResult(AgentStatus.FAILURE, error=f"Invalid input type: {input_artifact.type}")

        step_path = input_artifact.path
        if not os.path.exists(step_path):
            return AgentResult(AgentStatus.FAILURE, error=f"File not found: {step_path}")

        # 1. Load STEP File
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(step_path)
        
        if status != IFSelect_RetDone:
            return AgentResult(AgentStatus.FAILURE, error="Error reading STEP file.")

        step_reader.TransferRoots()
        shape = step_reader.OneShape()

        # 2. Basic Topology Check (BRepCheck)
        analyzer = BRepCheck_Analyzer(shape)
        if not analyzer.IsValid():
            # We don't fail hard here, but we log it. The Optimizer might fix it.
            print(f"[{self.name}] Warning: BRepCheck detected invalid topology.")

        # 3. Export to .brep (OpenCascade native format) for Gmsh
        filename = os.path.basename(step_path).replace(".step", ".brep").replace(".stp", ".brep")
        output_path = os.path.join(output_dir, filename)
        
        breptools_Write(shape, output_path)

        # 4. Extract Metadata
        face_count = 0
        exp = TopExp_Explorer(shape, TopAbs_FACE)
        while exp.More():
            face_count += 1
            exp.Next()

        return AgentResult(
            status=AgentStatus.SUCCESS,
            artifact=Artifact(
                type=ArtifactType.BREP_FILE,
                path=output_path,
                metadata={"face_count": face_count, "source": step_path}
            ),
            log=f"Parsed STEP file. Faces: {face_count}"
        )
