import argparse
import sys
import os
from core.supervisor import Supervisor

def main():
    parser = argparse.ArgumentParser(description="ACMS: Automated CAD-to-Mesh System")
    parser.add_argument("input_file", help="Path to the input STEP file")
    parser.add_argument("--workspace", default="workspace", help="Directory for intermediate artifacts")
    
    args = parser.parse_args()
    
    input_path = os.path.abspath(args.input_file)
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
        
    print(f"Starting ACMS on {input_path}...")
    
    supervisor = Supervisor(workspace_dir=args.workspace)
    result = supervisor.run(input_path)
    
    if result["status"] == "SUCCESS":
        print("\nACMS Completed Successfully.")
        sys.exit(0)
    else:
        print(f"\nACMS Failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
