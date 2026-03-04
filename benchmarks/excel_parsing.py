import pandas as pd
import time
import io
import numpy as np

def create_dummy_excel(filename, num_rows=10000):
    df1 = pd.DataFrame(np.random.randn(num_rows, 10), columns=[f'col_{i}' for i in range(10)])
    df2 = pd.DataFrame(np.random.randn(num_rows, 10), columns=[f'col_{i}' for i in range(10)])

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='FAC', index=False)
        df2.to_excel(writer, sheet_name='EAP', index=False)

def benchmark_current(filename, fac_sheet, eap_sheet):
    start_time = time.time()
    # In the app, it does this first to get sheet names
    excel_file = pd.ExcelFile(filename)
    _ = excel_file.sheet_names

    # Then it reads again twice
    df_fac = pd.read_excel(
        filename,
        sheet_name=fac_sheet,
        engine="openpyxl"
    )

    df_eap = pd.read_excel(
        filename,
        sheet_name=eap_sheet,
        engine="openpyxl"
    )
    end_time = time.time()
    return end_time - start_time

def benchmark_optimized(filename, fac_sheet, eap_sheet):
    start_time = time.time()
    # Optimized version: reuse the ExcelFile object
    excel_file = pd.ExcelFile(filename, engine="openpyxl")
    _ = excel_file.sheet_names

    df_fac = excel_file.parse(sheet_name=fac_sheet)
    df_eap = excel_file.parse(sheet_name=eap_sheet)
    end_time = time.time()
    return end_time - start_time

if __name__ == "__main__":
    filename = "dummy_excel.xlsx"
    print(f"Creating dummy excel with 10000 rows...")
    create_dummy_excel(filename)

    fac_sheet = "FAC"
    eap_sheet = "EAP"

    num_runs = 5
    current_times = []
    print("Running current method...")
    for i in range(num_runs):
        t = benchmark_current(filename, fac_sheet, eap_sheet)
        current_times.append(t)
        print(f"Run {i+1}: {t:.4f}s")

    optimized_times = []
    print("Running optimized method...")
    for i in range(num_runs):
        t = benchmark_optimized(filename, fac_sheet, eap_sheet)
        optimized_times.append(t)
        print(f"Run {i+1}: {t:.4f}s")

    avg_current = sum(current_times) / num_runs
    avg_optimized = sum(optimized_times) / num_runs

    print(f"\nAverage Current: {avg_current:.4f}s")
    print(f"Average Optimized: {avg_optimized:.4f}s")
    print(f"Improvement: {(avg_current - avg_optimized) / avg_current * 100:.2f}%")
