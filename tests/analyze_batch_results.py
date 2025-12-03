import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def analyze_results():
    # Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "numerical_results.csv")
    output_dir = os.path.join(base_dir, "figures")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Load Data
    df = pd.read_csv(csv_path)
    
    # Clean Data
    # Convert numeric columns, coercing errors to NaN
    numeric_cols = ['Duration_sec', 'Faces', 'Vertices', 'Volume', 'Iterations']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Set Style
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({'font.size': 12, 'figure.autolayout': True})
    
    # --- Figure 1: Success Rate ---
    plt.figure(figsize=(6, 6))
    status_counts = df['Status'].value_counts()
    plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', 
            colors=sns.color_palette('pastel'), startangle=90)
    plt.title('ACMS Pipeline Success Rate (n=15)')
    plt.savefig(os.path.join(output_dir, 'fig1_success_rate.png'), dpi=300)
    plt.close()
    
    # --- Figure 2: Processing Time Distribution ---
    plt.figure(figsize=(8, 5))
    sns.histplot(data=df, x='Duration_sec', hue='Status', multiple="stack", bins=10, palette="viridis")
    plt.title('Processing Time Distribution')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Count')
    plt.savefig(os.path.join(output_dir, 'fig2_time_distribution.png'), dpi=300)
    plt.close()
    
    # --- Figure 3: Complexity vs Time (Successful Models) ---
    success_df = df[df['Status'] == 'SUCCESS'].copy()
    if not success_df.empty:
        plt.figure(figsize=(8, 5))
        sns.scatterplot(data=success_df, x='Faces', y='Duration_sec', s=100, color='b')
        
        # Label points
        for i, row in success_df.iterrows():
            plt.text(row['Faces'], row['Duration_sec'], 
                     row['Model'].replace('.STEP', '').replace('.step', ''), 
                     fontsize=9, ha='right')
                     
        plt.title('Mesh Complexity vs. Processing Time (Successful Models)')
        plt.xlabel('Number of Faces')
        plt.ylabel('Time (seconds)')
        plt.savefig(os.path.join(output_dir, 'fig3_complexity_vs_time.png'), dpi=300)
        plt.close()
        
    # --- Figure 4: Failure Analysis ---
    fail_df = df[df['Status'] == 'FAILURE'].copy()
    if not fail_df.empty:
        plt.figure(figsize=(10, 6))
        # Simplify error messages for plotting
        fail_df['ShortError'] = fail_df['Error'].apply(lambda x: str(x)[:50] + "..." if len(str(x)) > 50 else str(x))
        sns.countplot(y='ShortError', data=fail_df, palette="rocket")
        plt.title('Distribution of Failure Causes')
        plt.xlabel('Count')
        plt.ylabel('Error Message')
        plt.savefig(os.path.join(output_dir, 'fig4_failure_causes.png'), dpi=300)
        plt.close()

    print(f"Analysis complete. Figures saved to {output_dir}")

    # --- Generate Table 1: Comparative Performance ---
    print("\nGenerating Table 1...")
    
    # Filter for relevant columns
    table_cols = ['Category', 'Method', 'Status', 'Avg_Jacobian', 'Iterations']
    if not all(col in df.columns for col in table_cols):
        print("Warning: Missing columns for Table 1 generation. Run batch test first.")
        return

    # Group by Category and Method
    # Calculate Success Rate, Avg Jacobian, Avg Iterations
    results = []
    
    categories = ['Simple', 'Industrial', 'Organic']
    methods = ['Baseline', 'ACMS']
    
    for cat in categories:
        row_data = {'Category': cat}
        for method in methods:
            subset = df[(df['Category'] == cat) & (df['Method'] == method)]
            total = len(subset)
            if total == 0:
                success_rate = 0.0
                avg_jac = 0.0
                avg_iter = 0.0
            else:
                success_count = len(subset[subset['Status'] == 'SUCCESS'])
                success_rate = (success_count / total) * 100
                
                # Metrics only for successful runs
                success_subset = subset[subset['Status'] == 'SUCCESS']
                if len(success_subset) > 0:
                    avg_jac = success_subset['Avg_Jacobian'].mean()
                    avg_iter = success_subset['Iterations'].mean()
                else:
                    avg_jac = 0.0
                    avg_iter = 0.0
            
            row_data[f'{method}_Success'] = success_rate
            row_data[f'{method}_Jac'] = avg_jac
            row_data[f'{method}_Iter'] = avg_iter
            
        results.append(row_data)

    # Print LaTeX Table
    print("\n\\begin{table}[h]")
    print("\\centering")
    print("\\begin{tabular}{l|cc|cc|cc}")
    print("\\hline")
    print("\\textbf{Category} & \\multicolumn{2}{c|}{\\textbf{Success Rate (\\%)}} & \\multicolumn{2}{c|}{\\textbf{Avg Jacobian}} & \\multicolumn{2}{c}{\\textbf{Avg Iterations}} \\\\")
    print(" & Baseline & ACMS & Baseline & ACMS & Baseline & ACMS \\\\")
    print("\\hline")
    
    for row in results:
        cat = row['Category']
        b_succ = row['Baseline_Success']
        a_succ = row['ACMS_Success']
        b_jac = row['Baseline_Jac']
        a_jac = row['ACMS_Jac']
        b_iter = row['Baseline_Iter']
        a_iter = row['ACMS_Iter']
        
        # Bold best values logic (simplified)
        a_succ_str = f"\\textbf{{{a_succ:.1f}}}" if a_succ >= b_succ else f"{a_succ:.1f}"
        a_jac_str = f"\\textbf{{{a_jac:.2f}}}" if a_jac >= b_jac else f"{a_jac:.2f}"
        
        print(f"{cat} & {b_succ:.1f} & {a_succ_str} & {b_jac:.2f} & {a_jac_str} & {b_iter:.1f} & {a_iter:.1f} \\\\")
        
    print("\\hline")
    print("\\end{tabular}")
    print("\\caption{Comparative performance of Baseline vs. ACMS across three dataset categories (n=" + str(len(df)//2) + ").}")
    print("\\label{tab:results}")
    print("\\end{table}")

if __name__ == "__main__":
    analyze_results()
