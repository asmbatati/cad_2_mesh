import os
import subprocess
import sys

def run_batch():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cad_dir = os.path.join(base_dir, "tests", "CAD files")
    main_script = os.path.join(base_dir, "main.py")
    
    if not os.path.exists(cad_dir):
        print(f"Error: Directory not found: {cad_dir}")
        return

    files = [f for f in os.listdir(cad_dir) if f.lower().endswith(('.step', '.stp', '.igs', '.iges'))]
    
    print(f"Found {len(files)} CAD files in {cad_dir}")
    
    results = []
    
    for f in files:
        input_path = os.path.join(cad_dir, f)
        print(f"\nProcessing {f}...")
        
        try:
            # Run main.py
            cmd = [sys.executable, main_script, input_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"SUCCESS: {f}")
                results.append((f, "SUCCESS"))
            else:
                print(f"FAILURE: {f}")
                print(f"Output:\n{result.stdout}")
                print(f"Error:\n{result.stderr}")
                results.append((f, "FAILURE"))
                
        except Exception as e:
            print(f"ERROR running {f}: {e}")
            results.append((f, "ERROR"))
            
    print("\n" + "="*30)
    print("BATCH PROCESSING SUMMARY")
    print("="*30)
    for name, status in results:
        print(f"{name}: {status}")

if __name__ == "__main__":
    run_batch()
