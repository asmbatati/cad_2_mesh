import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.supervisor import Supervisor
from core.types import AgentResult, AgentStatus, Artifact, ArtifactType

class TestACMS(unittest.TestCase):
    
    @patch('core.supervisor.ParserAgent')
    def test_supervisor_loop(self, MockParser):
        # Setup Mock Parser
        parser_instance = MockParser.return_value
        parser_instance.run.return_value = AgentResult(
            status=AgentStatus.SUCCESS,
            artifact=Artifact(
                type=ArtifactType.BREP_FILE, 
                path="mock_model.brep",
                metadata={"face_count": 10}
            ),
            log="Mock Parsed"
        )
        
        # We also need to mock Mesher/Validator/Optimizer if their libs aren't installed or if we want pure logic test
        # But let's try to use real ones if possible. 
        # If gmsh/trimesh are installed, we can try to mock only the file system interactions if needed.
        # For this test, let's mock EVERYTHING to verify the LOGIC of the Supervisor (Algorithm 1).
        
        with patch('core.supervisor.MesherAgent') as MockMesher, \
             patch('core.supervisor.ValidatorAgent') as MockValidator, \
             patch('core.supervisor.OptimizerAgent') as MockOptimizer:
             
            # Setup Mesher
            mesher_instance = MockMesher.return_value
            mesher_instance.run.return_value = AgentResult(
                status=AgentStatus.SUCCESS,
                artifact=Artifact(ArtifactType.STL_FILE, "mock_mesh.stl"),
                log="Mock Meshed"
            )
            
            # Setup Validator (Fail once, then Success)
            validator_instance = MockValidator.return_value
            validator_instance.run.side_effect = [
                AgentResult(
                    status=AgentStatus.SUCCESS,
                    artifact=Artifact(ArtifactType.VALIDATION_REPORT, "mem", {"status": "FAIL", "failures": ["is_watertight"]}),
                    log="Validation Failed"
                ),
                AgentResult(
                    status=AgentStatus.SUCCESS,
                    artifact=Artifact(ArtifactType.VALIDATION_REPORT, "mem", {"status": "SUCCESS"}),
                    log="Validation Passed"
                )
            ]
            
            # Setup Optimizer
            optimizer_instance = MockOptimizer.return_value
            optimizer_instance.run.return_value = AgentResult(
                status=AgentStatus.SUCCESS,
                artifact=Artifact(ArtifactType.STL_FILE, "mock_mesh_fixed.stl"),
                log="Mock Repaired"
            )
            
            # Run Supervisor
            supervisor = Supervisor(workspace_dir="test_workspace")
            # We mock os.path.exists to avoid creating dirs
            with patch('os.path.exists', return_value=True), \
                 patch('os.makedirs'):
                
                success = supervisor.run("dummy.step")
                
                # Assertions
                self.assertTrue(success)
                self.assertEqual(validator_instance.run.call_count, 2) # Called twice
                optimizer_instance.run.assert_called_once() # Called once for repair
                print("\nTest passed: Supervisor correctly triggered repair loop.")

if __name__ == '__main__':
    unittest.main()
