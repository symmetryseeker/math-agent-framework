"""Download MATH benchmark dataset."""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from datasets import load_dataset
d = load_dataset("hendrycks/competition_math", split="test")
print(f"Downloaded: {len(d)} problems")
print(f"Levels: {sorted(set(d['level']))}")
print(f"Types: {sorted(set(d['type']))}")
print(f"Sample:\n{d[0]}")
