import pandas as pd
import os
import pickle
from datasets import load_dataset
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from pythainlp.tokenize import word_tokenize # นำเข้า PyThaiNLP

# สร้างฟังก์ชันตัดคำภาษาไทย
def thai_tokenizer(text):
    return word_tokenize(text, engine="newmm")

def load_and_prep_data(csv_path="supremecourt_rag_data.csv"):
    # ... [ใช้โค้ดโหลดและหั่นข้อมูลเหมือนเดิมทุกประการ] ...
    documents = []
    
    print("1. กำลังโหลดข้อมูลฎีกาจาก CSV...")
    df_deka = pd.read_csv(csv_path)
    df_deka = df_deka.dropna(subset=['long_summary']) 
    
    for _, row in df_deka.iterrows():
        doc = Document(
            page_content=str(row['long_summary']), 
            metadata={
                "source_type": "deka",
                "deka_no": str(row['deka_no']),
                "litigant": str(row['litigant'])
            }
        )
        documents.append(doc)

    print("2. กำลังโหลดกฎหมายจาก Hugging Face...")
    ds = load_dataset("pythainlp/thailaw-v1.0", split="train")
    
    for item in ds:
        title = str(item['title'])
        text = str(item['text'])
        if "ประมวลกฎหมายอาญา" in title or "ประมวลกฎหมายแพ่งและพาณิชย์" in title:
            doc = Document(
                page_content=text,
                metadata={
                    "source_type": "law",
                    "title": title
                }
            )
            documents.append(doc)

    print("3. กำลังหั่นข้อมูล (Chunking)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, 
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunked_docs = text_splitter.split_documents(documents)
    print(f"   -> หั่นข้อมูลเสร็จสิ้น ได้ทั้งหมด {len(chunked_docs)} ชิ้นส่วน")
    
    return chunked_docs

def build_databases():
    chunked_docs = load_and_prep_data()
    
    print("\n4. กำลังโหลด Embedding Model (สำหรับ ChromaDB)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    print("5. กำลังสร้าง Vector Database (ChromaDB)...")
    persist_directory = "./chroma_db"
    
    # ถ้าไม่อยากเสียเวลาสร้าง Vector ใหม่ (เพราะมันกินเวลา) คุณสามารถคอมเมนต์ส่วนนี้ทิ้งได้
    # แต่ถ้าให้ชัวร์ รันใหม่ทับไปเลยดีกว่าครับ เพื่อให้ข้อมูล sync กัน
    vectorstore = Chroma.from_documents(
        documents=chunked_docs, 
        embedding=embeddings, 
        persist_directory=persist_directory
    )
    print(f"   -> บันทึก ChromaDB สำเร็จ!")

    print("6. กำลังสร้าง Keyword Index (BM25 + PyThaiNLP Tokenizer)...")
    # ไฮไลต์อยู่ที่บรรทัดนี้: โยนฟังก์ชันตัดคำไทยเข้าไปให้ BM25 ใช้
    bm25_retriever = BM25Retriever.from_documents(
        chunked_docs,
        preprocess_func=thai_tokenizer
    )
    
    with open("bm25_index.pkl", "wb") as f:
        pickle.dump(bm25_retriever, f)
    print("   -> บันทึก BM25 อัปเกรดสำเร็จ! ตรวจสอบไฟล์: bm25_index.pkl")

if __name__ == "__main__":
    build_databases()