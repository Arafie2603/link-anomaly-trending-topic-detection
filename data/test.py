# run_preprocessor.py

from preprocessing import Preprocessor  # Sesuaikan dengan path file Preprocessor Anda

def main():
    # Inisialisasi Preprocessor
    preprocessor = Preprocessor()
    
    # Jalankan preprocessing
    result = preprocessor.run_preprocessing()
    
    # Cetak hasil
    if "error" in result:
        print("Error:", result["error"])
    else:
        print("Success:", result["success"])
        for item in result["data"]:
            print(item)

if __name__ == "__main__":
    main()
