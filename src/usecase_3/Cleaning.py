import csv
from src.logger import logger

input_file = "arXiv_scientific_dataset.csv"
output_file = "dataset.csv"

cleaned_rows = []

logger.info(f"Reading input CSV: {input_file}")

try:
    with open(input_file, 'r', encoding='utf-8', errors='replace') as infile:
        # csv.reader automatically handles newlines inside quoted summaries!
        reader = csv.reader(infile)
        header = next(reader, None)
        logger.debug(f"Header: {header}")

        for i, row in enumerate(reader):
            if row:
                cleaned_row = [field.strip().replace('\n', ' ') for field in row]
                cleaned_rows.append(cleaned_row)
            else:
                logger.warning(f"Skipped empty row at line {i + 2}")  # +2 accounts for header + 0-index

except FileNotFoundError:
    logger.error(f"Input file not found: {input_file}")
    raise
except Exception:
    logger.exception(f"Unexpected error while reading {input_file}")
    raise

logger.info(f"Cleaned {len(cleaned_rows)} rows, writing to {output_file}")

try:
    # Write out everything with forced double quotes around every field
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
        if header:
            writer.writerow([h.strip().lower() for h in header])
        writer.writerows(cleaned_rows)
except Exception:
    logger.exception(f"Unexpected error while writing {output_file}")
    raise

logger.info(f"Total rows preserved: {len(cleaned_rows)}")
print(f"Total rows preserved: {len(cleaned_rows)}")