import csv

input_file = "arXiv_scientific_dataset.csv"
output_file = "dataset.csv"

cleaned_rows = []

with open(input_file, 'r', encoding='utf-8', errors='replace') as infile:
    # csv.reader automatically handles newlines inside quoted summaries!
    reader = csv.reader(infile)
    header = next(reader, None) 
    
    for row in reader:
        if row:
            cleaned_row = [field.strip().replace('\n', ' ') for field in row]
            cleaned_rows.append(cleaned_row)

# Write out everything with forced double quotes around every field
with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
    if header:
        writer.writerow([h.strip().lower() for h in header])
    writer.writerows(cleaned_rows)

print(f"Total rows preserved: {len(cleaned_rows)}")