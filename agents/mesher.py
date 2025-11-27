import os
import gmsh
from core.types import Artifact, ArtifactType, AgentResult, AgentStatus

class MesherAgent:
    def __init__(self, name="Mesher"):
        self.name = name

    def run(self, input_artifact: Artifact, output_dir: str, fineness: float = 0.5) -> AgentResult:
        if input_artifact.type not in [ArtifactType.BREP_FILE, ArtifactType.STEP_FILE]:
            return AgentResult(AgentStatus.FAILURE, error=f"Invalid input type: {input_artifact.type}")

        input_path = input_artifact.path
        filename = os.path.basename(input_path).replace(".brep", ".stl").replace(".step", ".stl")
        output_path = os.path.join(output_dir, filename)

        try:
            gmsh.initialize()
            gmsh.option.setNumber("General.Terminal", 1)
            gmsh.open(input_path)

            # Set Mesh Fineness
            # Gmsh Mesh.MeshSizeFactor: smaller is finer
            # Mapping fineness (0.0-1.0) to MeshSizeFactor (1.0 - 0.1)
            mesh_factor = 1.0 - (fineness * 0.9)
            gmsh.option.setNumber("Mesh.MeshSizeFactor", mesh_factor)

            # Generate 2D Mesh (Surface)
            gmsh.model.mesh.generate(2)

            # Export
            gmsh.write(output_path)
            
            # Get Node/Element counts
            # (Optional: could extract from gmsh.model.mesh.getNodes())
            
        except Exception as e:
            return AgentResult(AgentStatus.FAILURE, error=str(e))
        finally:
            gmsh.finalize()

        return AgentResult(
            status=AgentStatus.SUCCESS,
            artifact=Artifact(
                type=ArtifactType.STL_FILE,
                path=output_path,
                metadata={"fineness": fineness}
            ),
            log=f"Meshed with fineness {fineness}"
        )
