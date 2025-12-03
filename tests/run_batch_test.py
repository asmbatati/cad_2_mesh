import os
import csv
import shutil
import time
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.supervisor import Supervisor

def get_category(filename):
    lower = filename.lower()
    if "cube" in lower or "simple" in lower or "box" in lower:
        return "Simple"
    elif "sculpt" in lower or "bone" in lower or "scan" in lower:
        return "Organic"
    else:
        return "Industrial"

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
        category = get_category(filename)
        
        # Create a dedicated workspace for this model to avoid collisions
        model_name = os.path.splitext(filename)[0]
        model_workspace = os.path.join(output_dir, model_name)
        if not os.path.exists(model_workspace):
            os.makedirs(model_workspace)
            
        supervisor = Supervisor(workspace_dir=model_workspace)
        
        # --- Run ACMS ---
        print(f"  > Running ACMS on {filename}...")
        start_time = time.time()
        try:
            res_acms = supervisor.run(input_path)
        except Exception as e:
            print(f"CRITICAL ERROR processing {filename} (ACMS): {e}")
            res_acms = {"model": filename, "status": "CRASH", "error": str(e)}
        duration_acms = time.time() - start_time
        
        # Log ACMS
        row_acms = {
            "Model": filename,
            "Category": category,
            "Method": "ACMS",
            "Status": res_acms["status"],
            "Iterations": res_acms.get("iterations", 0),
            "Duration_sec": round(duration_acms, 2),
            "Error": res_acms.get("error", ""),
            "Final_Mesh": res_acms.get("final_mesh_path", "")
        }
        report_acms = res_acms.get("validation_report", {}).get("metrics", {})
        row_acms.update({
            "Watertight": report_acms.get("is_watertight", ""),
            "Faces": report_acms.get("face_count", ""),
            "Vertices": report_acms.get("vertex_count", ""),
            "Volume": report_acms.get("volume", ""),
            "Avg_Jacobian": report_acms.get("avg_jacobian", ""),
            "Min_Jacobian": report_acms.get("min_jacobian", "")
        })
        results.append(row_acms)

        # --- Run Baseline ---
        print(f"  > Running Baseline on {filename}...")
        start_time = time.time()
        try:
            res_base = supervisor.run_baseline(input_path)
        except Exception as e:
            print(f"CRITICAL ERROR processing {filename} (Baseline): {e}")
            res_base = {"model": filename, "status": "CRASH", "error": str(e)}
        duration_base = time.time() - start_time
        
        # Log Baseline
        row_base = {
            "Model": filename,
            "Category": category,
            "Method": "Baseline",
            "Status": res_base["status"],
            "Iterations": res_base.get("iterations", 0),
            "Duration_sec": round(duration_base, 2),
            "Error": res_base.get("error", ""),
            "Final_Mesh": res_base.get("final_mesh_path", "")
        }
        report_base = res_base.get("validation_report", {}).get("metrics", {})
        row_base.update({
            "Watertight": report_base.get("is_watertight", ""),
            "Faces": report_base.get("face_count", ""),
            "Vertices": report_base.get("vertex_count", ""),
            "Volume": report_base.get("volume", ""),
            "Avg_Jacobian": report_base.get("avg_jacobian", ""),
            "Min_Jacobian": report_base.get("min_jacobian", "")
        })
        results.append(row_base)
        
        # Copy final mesh to main output dir if successful (ACMS only preferred, or both with suffix)
        if res_acms["status"] == "SUCCESS" and res_acms.get("final_mesh_path"):
            final_mesh = res_acms["final_mesh_path"]
            if os.path.exists(final_mesh):
                dest_name = f"{model_name}_ACMS.stl"
                shutil.copy(final_mesh, os.path.join(output_dir, dest_name))

        if res_base["status"] == "SUCCESS" and res_base.get("final_mesh_path"):
            final_mesh = res_base["final_mesh_path"]
            if os.path.exists(final_mesh):
                dest_name = f"{model_name}_Baseline.stl"
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
