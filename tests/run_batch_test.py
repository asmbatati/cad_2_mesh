import os
import csv
import shutil
import time
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.supervisor import Supervisor

def run_batch():
    input_dir = os.path.abspath("tests/CAD files")
    output_dir = os.path.abspath("tests/Mesh results")
    results_csv = os.path.abspath("tests/numerical_results.csv")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.step', '.stp'))]
    print(f"Found {len(files)} STEP files in {input_dir}")
    
    results = []
    
    for i, filename in enumerate(files):
        print(f"\n[{i+1}/{len(files)}] Processing {filename}...")
        input_path = os.path.join(input_dir, filename)
        
        # Create a dedicated workspace for this model to avoid collisions
        model_name = os.path.splitext(filename)[0]
        model_workspace = os.path.join(output_dir, model_name)
        if not os.path.exists(model_workspace):
            os.makedirs(model_workspace)
            
        supervisor = Supervisor(workspace_dir=model_workspace)
        start_time = time.time()
        
        try:
            res = supervisor.run(input_path)
        except Exception as e:
            print(f"CRITICAL ERROR processing {filename}: {e}")
            res = {"model": filename, "status": "CRASH", "error": str(e)}
            
        duration = time.time() - start_time
        
        # Flatten metrics for CSV
        row = {
            "Model": filename,
            "Status": res["status"],
            "Iterations": res.get("iterations", 0),
            "Duration_sec": round(duration, 2),
            "Error": res.get("error", ""),
            "Final_Mesh": res.get("final_mesh_path", "")
        }
        
        # Add validation metrics if available
        report = res.get("validation_report", {}).get("metrics", {})
        row.update({
            "Watertight": report.get("is_watertight", ""),
            "Faces": report.get("face_count", ""),
            "Vertices": report.get("vertex_count", ""),
            "Volume": report.get("volume", "")
        })
        
        results.append(row)
        
        # Copy final mesh to main output dir if successful
        if res["status"] == "SUCCESS" and res.get("final_mesh_path"):
            final_mesh = res["final_mesh_path"]
            if os.path.exists(final_mesh):
                dest_name = f"{model_name}_final.stl"
                shutil.copy(final_mesh, os.path.join(output_dir, dest_name))

    # Save CSV
    if results:
        keys = results[0].keys()
        with open(results_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nBatch processing complete. Results saved to {results_csv}")
    else:
        print("\nNo results to save.")

if __name__ == "__main__":
    run_batch()
