import trimesh
import trimesh.repair
import os
from core.types import Artifact, ArtifactType, AgentResult, AgentStatus

class OptimizerAgent:
    def __init__(self, name="Optimizer"):
        self.name = name

    def run(self, input_artifact: Artifact, output_dir: str, task: str = "repair") -> AgentResult:
        if input_artifact.type != ArtifactType.STL_FILE:
            return AgentResult(AgentStatus.FAILURE, error=f"Invalid input type: {input_artifact.type}")

        input_path = input_artifact.path
        filename = os.path.basename(input_path).replace(".stl", "_optimized.stl")
        output_path = os.path.join(output_dir, filename)

        try:
            mesh = trimesh.load(input_path)
            
            log = []
            
            if task == "repair_watertight":
                # 1. Fill Holes
                trimesh.repair.fill_holes(mesh)
                log.append("Filled holes.")
                
                # 2. Fix Normals
                trimesh.repair.fix_normals(mesh)
                log.append("Fixed normals.")
                
                # 3. Fix Inversion
                trimesh.repair.fix_inversion(mesh)
                log.append("Fixed inversion.")
                
            elif task == "optimize_jacobian":
                # Trimesh doesn't have direct Jacobian optimization (usually FEM specific)
                # We simulate this by smoothing, which often improves element quality
                trimesh.smoothing.filter_laplacian(mesh, iterations=5)
                log.append("Applied Laplacian smoothing.")
                
            else:
                return AgentResult(AgentStatus.FAILURE, error=f"Unknown task: {task}")

            mesh.export(output_path)
            
        except Exception as e:
            return AgentResult(AgentStatus.FAILURE, error=str(e))

        return AgentResult(
            status=AgentStatus.SUCCESS,
            artifact=Artifact(
                type=ArtifactType.STL_FILE,
                path=output_path,
                metadata={"last_op": task}
            ),
            log="; ".join(log)
        )
