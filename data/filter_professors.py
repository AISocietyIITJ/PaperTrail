import pandas as pd

# Load your dataset (replace 'input.csv' with your actual file name)
df = pd.read_csv("scholars_data.csv")

# Define a regular expression pattern for keywords to exclude
# This catches variations like "Ph.D", "PHD", "M.Tech", "student", and typos like "reasearch scholar"
exclude_pattern = r"phd|ph\.d|mtech|m\.tech|student|scholar"

# Combine Name and Affiliation columns to search for student keywords in both
text_to_check = df["Name"].astype(str) + " " + df["Affiliation"].astype(str)

# Filter the DataFrame to KEEP rows that DO NOT (~) contain the exclude pattern
filtered_df = df[~text_to_check.str.contains(exclude_pattern, case=False, regex=True)]

# Save the cleaned data to a new CSV file
output_filename = "filtered_faculty.csv"
filtered_df.to_csv(output_filename, index=False)

print(f"Filtering complete. Saved {len(filtered_df)} records to {output_filename}.")