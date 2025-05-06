import pandas as pd
import os

print('Testing CSV import fix with problematic formatting')

test_csv = 'test_import.csv'
print(f'Reading file: {test_csv}')

try:
    # Try newer pandas version approach
    print('Attempting with on_bad_lines parameter...')
    df = pd.read_csv(test_csv, on_bad_lines='skip', delimiter=',')
    print(f'Successfully parsed with on_bad_lines: {len(df)} rows')
    print(df)
except TypeError:
    # Fall back to older pandas version approach
    print('Falling back to error_bad_lines parameter...')
    df = pd.read_csv(test_csv, error_bad_lines=False, delimiter=',')
    print(f'Successfully parsed with error_bad_lines: {len(df)} rows')
    print(df)

print('\nTest completed successfully!')