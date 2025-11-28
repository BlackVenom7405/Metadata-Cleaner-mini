import os
from cleaner.image_cleaner import clean_image
from cleaner.pdf_cleaner import clean_pdf
from cleaner.docx_cleaner import clean_docx

CLEANED_DIR = "cleaned"

def ensure_cleaned_dir():
    if not os.path.exists(CLEANED_DIR):
        os.makedirs(CLEANED_DIR)

def main():
    print("=== Metadata Cleaner ===")
    print("1. Clean Image (JPG/PNG)")
    print("2. Clean PDF")
    print("3. Clean Word (DOCX)")
    print("0. Exit")

    choice = input("Enter your choice: ")

    if choice == "0":
        print("Exiting...")
        return

    file_path = input("Enter file path: ")
    if not os.path.exists(file_path):
        print("File not found!")
        return

    ensure_cleaned_dir()

    if choice == "1":
        output_file = os.path.join(CLEANED_DIR, "cleaned_image.jpg")
        print(clean_image(file_path, output_file))

    elif choice == "2":
        output_file = os.path.join(CLEANED_DIR, "cleaned_pdf.pdf")
        print(clean_pdf(file_path, output_file))

    elif choice == "3":
        output_file = os.path.join(CLEANED_DIR, "cleaned_doc.docx")
        print(clean_docx(file_path, output_file))

    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
