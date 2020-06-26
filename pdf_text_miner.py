import fitz
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import os
import pandas as pd
import datetime

a = "/usr/local/Cellar/tesseract/4.1.1/bin/tesseract"  # Tesseract installation path.


# FINDS PDFS IN THE DIRECTORY

def get_pdfs():
    pdfs = []
    directory = list(os.listdir())

    for file in directory:
        ext = os.path.splitext(file)[1][1:].strip()  # Gets file extension.
        if ext == 'pdf':
            pdfs.append(file)
    safe_copy = pd.DataFrame(pdfs, columns=['files'])
    safe_copy.to_csv('list_of_pdfs.csv', index=False)  # Saves a spreadsheet with the PDFs in the directory.
    return pdfs


# CONVERTS PDFS TO TEXT AND STORES VALUES IN DATAFRAME

def extract_pdfs(list):  # You can easily extract a list from a .csv with pandas.

    d = {'file_name': ['dummy'], 'file_text': ['dummy'], 'ocr': [False]}
    df = pd.DataFrame(d, columns=['file_name', 'file_text', 'ocr'])
    count = 0

    for pdf in list:
        ext = os.path.splitext(pdf)[1][1:].strip()  # Gets file extension.
        if ext == 'pdf':  # Guarantees that the file is a .pdf, otherwise the program will crash when extracting text.
            ocr = False
            name = pdf.split('.pdf')[0]
            doc = fitz.open(f"{name}.pdf")
            text_file = open(f"{name}.txt", 'w')
            number_of_pages = doc.pageCount
            for page_n in range(number_of_pages):  # Extracts text from each page.
                page = doc.loadPage(page_n)
                page_content = page.getText("text")
                text_file.write(page_content)
            if os.stat(
                    f"{name}.txt").st_size < 2000:  # Assumes file lacks OCR based on .txt file size, starts Tesseract.
                ocr = True
                os.remove(f"{name}.txt")  # Removes the previously scraped .txt.
                tess_file = f"{name}.pdf"
                pages = convert_from_path(tess_file, 500)
                image_counter = 1
                for page in pages:  # Converts the PDF to image.
                    filename = f"{name}page_{str(image_counter)}.jpg"
                    page.save(filename, 'JPEG')
                    image_counter = image_counter + 1
                filelimit = image_counter - 1
                outfile = f"{name}.txt"
                f = open(outfile, "a")
                for i in range(1, filelimit + 1):  # Applies OCR to each image, saves text file.
                    filename = f"{name}page_{str(i)}.jpg"
                    text = str((pytesseract.image_to_string(Image.open(filename), lang="por")))
                    text = text.replace('-\n', '')
                    f.write(text)
                f.close()
            text = open(f"{name}.txt", 'r')
            txt = " ".join(text.readlines())
            df = df.append({'file_name': f"{name}", 'file_text': txt, 'ocr': ocr}, ignore_index=True)
            df.to_csv('pdfs_mined_so_far.csv', index=False)  # Saves the files processed so far in case of failure.
            count = count + 1
            end = datetime.datetime.now()
            print(
                f"Finished {name} at {end}. OCR = {ocr}. {count} files read. {round(count * 100 / len(list), 2)}% done.")
    df = df.iloc[1:]
    df.to_csv('files.csv', index=False)  # Outputs spreadsheet.
    os.remove('pdfs_mined_so_far.csv')  # Deletes the redundant copy.
    return df
