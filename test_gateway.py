import polars as pl

# Simulate what the gateway does
test_data = pl.DataFrame({
    "id": ["test001"],
    "problem": ["What is 5 + 3?"]
})

# Test iter_slices behavior
for row in test_data.iter_slices(n_rows=1):
    print(f"Type: {type(row)}")
    print(f"Columns: {row.columns}")
    print(f"Shape: {row.shape}")
    print(f"Data: {row}")
    
    # Try different access methods
    try:
        print(f"row(0): {row.row(0, named=True)}")
    except Exception as e:
        print(f"row(0) failed: {e}")
    
    try:
        print(f"to_dicts(): {row.to_dicts()}")
    except Exception as e:
        print(f"to_dicts() failed: {e}")
