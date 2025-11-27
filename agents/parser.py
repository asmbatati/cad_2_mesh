import os
import gmsh
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

        base, _ = os.path.splitext(os.path.basename(step_path))
        filename = f"{base}.brep"
        output_path = os.path.join(output_dir, filename)

        try:
            gmsh.initialize()
            gmsh.option.setNumber("General.Terminal", 1)
            
            # 1. Load STEP File
            # Gmsh uses OpenCASCADE internally to read STEP
            gmsh.open(step_path)
            
            # 2. Basic Topology Check
            # We can check if entities were loaded
            entities = gmsh.model.getEntities()
            if not entities:
                 return AgentResult(AgentStatus.FAILURE, error="No entities found in STEP file.")
            
            # 3. Export to .brep (Native OpenCASCADE format)
            # This normalizes the geometry for the Mesher
            gmsh.write(output_path)
            
            # 4. Extract Metadata
            # Count volumes/surfaces
            volumes = gmsh.model.getEntities(3)
            surfaces = gmsh.model.getEntities(2)
            
        except Exception as e:
            return AgentResult(AgentStatus.FAILURE, error=str(e))
        finally:
            gmsh.finalize()

        return AgentResult(
            status=AgentStatus.SUCCESS,
            artifact=Artifact(
                type=ArtifactType.BREP_FILE,
                path=output_path,
                metadata={"surface_count": len(surfaces), "volume_count": len(volumes)}
            ),
            log=f"Parsed STEP file using Gmsh. Surfaces: {len(surfaces)}"
        )
