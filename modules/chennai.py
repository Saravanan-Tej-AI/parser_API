import pdfplumber
import logging

# Configure the logger to append to the log file
logging.basicConfig(filename='chennai_process_log.log', filemode='a', 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    level=logging.INFO)

def extract_data_f1f2(pdf_path):
    data = []
    try:
        logging.info(f"Opening PDF file for extract_data_f1f2: {pdf_path}")
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if 'TOTAL' in page_text:
                    logging.info(f"Skipping page {page_number + 1} containing 'TOTAL'")
                    continue
                
                # Extract the table content from the page
                table = page.extract_table()
                if table:
                    logging.info(f"Table found on page {page_number + 1}")
                    for row in table:
                        cleaned_row = [cell.strip().replace('\n', ' ') if cell is not None else '' for cell in row]
                        data.append(cleaned_row)
                else:
                    logging.warning(f"No table found on page {page_number + 1}")

    except Exception as e:
        logging.error(f"An error occurred while processing the PDF in extract_data_f1f2: {e}")
        return []

    filtered_data = []
    specific_words = [
        'TYPE OF CASE', 'PS & I.O', 'D/O & D/R', 'Gist', 'Accused (Arrest/', 
        'Absconding) along with', 'previous cases', 'ZONE / CITY', 
        'DECEASED /', 'INJURED / VICTIM /', 'PROPERTY LOST /', 
        'SEIZED PROPERTY', '/ STAGE OF', 'PREVIOUS CASES /', 
        'H.S. / WHETHER', 'ANY ALERT MEMOS', 'RECEIVED FROM', 
        'OCIU AND ACTION', 'TAKEN', 'INJURED /'
    ]

    for row in data:
        if any(word in row for word in specific_words):
            logging.debug(f"Skipping header row in filtered_data: {row}")
            continue
        filtered_data.append(row)

    cleaned_data = []
    for row in filtered_data:
        non_empty_strings = [s for s in row if s]
        if len(non_empty_strings) == 1:
            cleaned_data.append([non_empty_strings[0]])
        else:
            cleaned_data.append(row)

    processed_data = []
    for row in cleaned_data:
        if not row[0]:
            if processed_data:
                for i in range(len(row)):
                    if row[i]:
                        processed_data[-1][i] += f" {row[i]}" if processed_data[-1][i] else row[i]
        else:
            processed_data.append(row)

    final_data = []
    temp = None
    for lst in processed_data:
        if len(lst) == 1:
            temp = lst[0]
        else:
            if temp is not None:
                lst.insert(0, f"Case category: {temp}")
            final_data.append(lst)

    final_data = [[s for s in row if s] for row in final_data]
    logging.info("Data extraction and processing in extract_data_f1f2 completed successfully.")
    return final_data


def extract_data_cocr(pdf_path):
    logging.info(f"Starting extract_data_cocr on PDF: {pdf_path}")
    first_column = []
    data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            if 'TOTAL' in text:
                tables = first_page.extract_tables()
                if tables:
                    logging.info("Extracting case types from the first column of the first page")
                    for row in tables[0]:
                        if row and row[0].strip():
                            first_column.append(row[0].strip())

            for page_number, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if 'TOTAL' in page_text:
                    logging.info(f"Skipping page {page_number + 1} containing 'TOTAL'")
                    continue
                
                lines = page_text.split('\n') if page_text else []
                table = page.extract_table()
                if table:
                    logging.info(f"Table found on page {page_number + 1}")
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 5 and line.isupper():
                            data.append([line])

                    table_content = table[1:] if len(table) > 1 else []
                    for row in table_content:
                        cleaned_row = [cell.strip().replace('\n', ' ') if cell else '' for cell in row]
                        if any(cleaned_row):
                            data.append(cleaned_row)

        cleaned_data = []
        for row in data:
            non_empty_strings = [s for s in row if s]
            if len(non_empty_strings) <= 3:
                if any(case in non_empty_strings[0] for case in first_column):
                    cleaned_data.append(non_empty_strings)
            else:
                cleaned_data.append(row)

        final_list = []
        category = ''
        for row in cleaned_data:
            if len(row) == 1:
                category = row[0]
            else:
                local = [f"Case Category: {category}"] + row
                final_list.append(local)

        logging.info("Data extraction and processing in extract_data_cocr completed successfully.")
        return final_list

    except Exception as e:
        logging.error(f"An error occurred while processing the PDF in extract_data_cocr: {e}")
        return []
