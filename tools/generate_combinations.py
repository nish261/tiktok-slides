import pandas as pd
import itertools
from pathlib import Path
import sys

def generate_combinations(input_csv: str, output_csv: str):
    """
    Reads a CSV where each column is a list of options for that section.
    Generates a Cartesian product of all sections and formats it for tiktok-slides.
    """
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        print(f"Error reading {input_csv}: {e}")
        return

    # Get all non-empty values for each column
    columns = df.columns
    pools = []
    headers = []
    
    for col in columns:
        # Filter out NaNs and empty strings
        values = [x for x in df[col].dropna().astype(str).tolist() if x.strip()]
        if not values:
            print(f"Warning: Column '{col}' is empty.")
            continue
            
        pools.append(values)
        headers.append(col)

    if not pools:
        print("No valid data found.")
        return

    # Generate Cartesian product
    combinations = list(itertools.product(*pools))
    
    print(f"Found {len(headers)} sections: {headers}")
    print(f"Generating {len(combinations)} combinations...")
    
    # Create output DataFrame structure
    # tiktok-slides expects: product_col1, col1, product_col2, col2...
    output_data = []
    
    for combo in combinations:
        row = {}
        for i, val in enumerate(combo):
            col_name = headers[i]
            # Assign 'all' to product column by default
            row[f'product_{col_name}'] = 'all'
            row[col_name] = val
        output_data.append(row)
        
    # Create list of column names in correct order
    output_columns = []
    for col in headers:
        output_columns.append(f'product_{col}')
        output_columns.append(col)
        
    result_df = pd.DataFrame(output_data, columns=output_columns)
    
    result_df.to_csv(output_csv, index=False)
    print(f"Saved combinations to {output_csv}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_combinations.py <input_csv> [output_csv]")
        print("Example: python generate_combinations.py lists.csv captions.csv")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "captions_combined.csv"
        generate_combinations(input_file, output_file)
