import os
import shutil
from typing import Optional

from agents.parser import ParserAgent
from agents.mesher import MesherAgent
from agents.validator import ValidatorAgent
from agents.optimizer import OptimizerAgent
from core.types import Artifact, ArtifactType, AgentStatus

class Supervisor:
    def __init__(self, workspace_dir="workspace"):
        self.workspace_dir = os.path.abspath(workspace_dir)
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)
            
        self.parser = ParserAgent()
        self.mesher = MesherAgent()
        self.validator = ValidatorAgent()
        self.optimizer = OptimizerAgent()
        
        self.max_iterations = 5

    def run(self, input_step_path: str) -> dict:
        print(f"=== ACMS Supervisor: Processing {input_step_path} ===")
        
        # 1. Parse
        input_artifact = Artifact(ArtifactType.STEP_FILE, input_step_path)
        parse_res = self.parser.run(input_artifact, self.workspace_dir)
        
        if parse_res.status == AgentStatus.FAILURE:
            print(f"Parsing Failed: {parse_res.error}")
            return {"model": os.path.basename(input_step_path), "status": "FAILURE", "error": parse_res.error}
            
        brep_artifact = parse_res.artifact
        print(f"Parsed: {parse_res.log}")

        # 2. Initial Mesh
        mesh_res = self.mesher.run(brep_artifact, self.workspace_dir, fineness=0.5)
        if mesh_res.status == AgentStatus.FAILURE:
            print(f"Meshing Failed: {mesh_res.error}")
            return {"model": os.path.basename(input_step_path), "status": "FAILURE", "error": mesh_res.error}
            
        current_mesh = mesh_res.artifact
        print(f"Initial Mesh: {mesh_res.log}")

        # 3. Validation Loop
        for i in range(self.max_iterations):
            print(f"\n--- Iteration {i+1} ---")
            
            val_res = self.validator.run(current_mesh)
            if val_res.status == AgentStatus.FAILURE:
                print(f"Validator Tool Failed: {val_res.error}")
                return {"model": os.path.basename(input_step_path), "status": "FAILURE", "error": val_res.error}
                
            report = val_res.artifact.metadata
            print(f"Validation Status: {report['status']}")
            
            # Prepare result for potential return
            result = {
                "model": os.path.basename(input_step_path),
                "status": "FAILURE",
                "iterations": i + 1,
                "final_mesh_path": current_mesh.path if current_mesh else None,
                "validation_report": report
            }

            if report["status"] == "SUCCESS":
                print(f"\n>>> SUCCESS: Mesh validated. Final path: {current_mesh.path}")
                result["status"] = "SUCCESS"
                return result
            
            # Reasoning Logic
            failures = report.get("failures", [])
            print(f"Failures: {failures}")
            
            if "is_watertight" in failures:
                print("Strategy: Repair Watertightness")
                opt_res = self.optimizer.run(current_mesh, self.workspace_dir, task="repair_watertight")
                if opt_res.status == AgentStatus.SUCCESS:
                    current_mesh = opt_res.artifact
                else:
                    print(f"Optimization Failed: {opt_res.error}")
                    result["error"] = opt_res.error
                    return result # Fatal error in optimization
                    
            elif "bad_aspect_ratio" in failures:
                print("Strategy: Optimize Element Quality (Smoothing)")
                opt_res = self.optimizer.run(current_mesh, self.workspace_dir, task="optimize_jacobian")
                if opt_res.status == AgentStatus.SUCCESS:
                    current_mesh = opt_res.artifact
                else:
                    print(f"Optimization Failed: {opt_res.error}")
                    result["error"] = opt_res.error
                    return result
            else:
                print("Strategy: Remesh with Higher Fineness")
                # Note: We need to go back to B-Rep for remeshing
                mesh_res = self.mesher.run(brep_artifact, self.workspace_dir, fineness=0.8)
                if mesh_res.status == AgentStatus.SUCCESS:
                    current_mesh = mesh_res.artifact
                else:
                    print(f"Remeshing Failed: {mesh_res.error}")
                    result["error"] = mesh_res.error
                    return result
                    
        print("\n>>> FAILURE: Max iterations reached.")
        return result
