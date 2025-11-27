# ACMS: Automated CAD-to-Mesh System

This is the full implementation of the ACMS architecture described in the paper. It uses `pythonOCC`, `gmsh`, and `trimesh` to perform closed-loop CAD-to-mesh conversion.

## Prerequisites

You need a Python environment with the following libraries. We recommend using `conda` or `mamba` because `pythonOCC` and `gmsh` have binary dependencies.

```bash
conda create -n acms_env python=3.9
conda activate acms_env
conda install -c conda-forge gmsh trimesh numpy scipy networkx
```

## Structure

- `main.py`: CLI entry point.
- `core/supervisor.py`: The central orchestration logic (Algorithm 1).
- `agents/`:
    - `parser.py`: Loads STEP files using Gmsh (OpenCASCADE backend).
    - `mesher.py`: Generates meshes using Gmsh.
    - `validator.py`: Checks mesh quality using Trimesh.
    - `optimizer.py`: Repairs/Optimizes meshes using Trimesh/Gmsh.

## Usage

Run the system on a STEP file:

```bash
python main.py path/to/your/model.step
```

The system will:
1.  Parse the STEP file.
2.  Generate an initial mesh.
3.  Validate the mesh.
4.  If validation fails, it will iteratively repair/optimize until success or max iterations.
5.  Artifacts are saved in the `workspace/` directory.

## License

MIT
