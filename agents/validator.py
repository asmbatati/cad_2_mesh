import trimesh
from core.types import Artifact, ArtifactType, AgentResult, AgentStatus

class ValidatorAgent:
    def __init__(self, name="Validator"):
        self.name = name

    def run(self, input_artifact: Artifact) -> AgentResult:
        if input_artifact.type != ArtifactType.STL_FILE:
            return AgentResult(AgentStatus.FAILURE, error=f"Invalid input type: {input_artifact.type}")

        # Load Mesh
        try:
            mesh = trimesh.load(input_artifact.path)
        except Exception as e:
            return AgentResult(AgentStatus.FAILURE, error=f"Trimesh load failed: {e}")

        # Checks
        is_watertight = mesh.is_watertight
        euler_number = mesh.euler_number
        volume = mesh.volume if is_watertight else 0.0
        
        # Detailed Failure Analysis
        failures = []
        details = []
        
        if not is_watertight:
            failures.append("is_watertight")
            # Check for holes/open edges
            # trimesh.graph.connected_components(mesh.edges_unique)
            details.append("open_edges_detected")

        # Check for self-intersections (using winding consistency as proxy or explicit check)
        # Note: trimesh.intersection.is_intersection is expensive, so we use winding/volume checks as proxies or simpler heuristics
        try:
            if not mesh.is_winding_consistent:
                 failures.append("self_intersection")
        except:
            pass

        # Check for disconnected components
        if mesh.body_count > 1:
            failures.append("disconnected_components")
            details.append(f"found_{mesh.body_count}_components")

        # Aspect Ratio (Mock approximation using edge lengths)
        edges = mesh.edges_unique_length
        if len(edges) > 0:
            min_edge = edges.min()
            max_edge = edges.max()
            if min_edge > 0 and (max_edge / min_edge) > 50: # Arbitrary threshold
                failures.append("bad_aspect_ratio")

        status = AgentStatus.SUCCESS # The AGENT succeeded, even if the MESH failed validation
        
        report_data = {
            "status": "SUCCESS" if not failures else "FAIL",
            "failures": failures,
            "details": details,
            "metrics": {
                "is_watertight": is_watertight,
                "euler_number": euler_number,
                "volume": volume,
                "vertex_count": len(mesh.vertices),
                "face_count": len(mesh.faces)
            }
        }

        return AgentResult(
            status=AgentStatus.SUCCESS,
            artifact=Artifact(
                type=ArtifactType.VALIDATION_REPORT,
                path="memory", # Report is in metadata
                metadata=report_data
            ),
            log=f"Validation complete. Status: {report_data['status']}"
        )
