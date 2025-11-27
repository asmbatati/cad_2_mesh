import gmsh
import sys

def create_cube_step(filename):
    gmsh.initialize()
    gmsh.model.add("cube")
    
    # Create a box
    gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
    gmsh.model.occ.synchronize()
    
    # Export to STEP
    gmsh.write(filename)
    gmsh.finalize()

if __name__ == "__main__":
    create_cube_step("tests/test_cube.step")
    print("Created tests/test_cube.step")
