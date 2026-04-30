import os
import argparse
import pickle
import asyncio
from typing import Dict, Any

# LangChain Imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.llms import Ollama
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from pythainlp.tokenize import word_tokenize

# Telegram Imports
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. RAG System Setup ---

def thai_tokenizer(text):
    return word_tokenize(text, engine="newmm")

def setup_rag_chain():
    """Initializes the Hybrid RAG chain with loaded databases."""
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"}
    )

    print("Loading ChromaDB (Semantic Search)...")
    chroma_vectorstore = Chroma(
        persist_directory="./chroma_db", 
        embedding_function=embeddings
    )
    chroma_retriever = chroma_vectorstore.as_retriever(search_kwargs={"k": 3})

    print("Loading BM25 Index (Lexical Search)...")
    try:
        with open('./bm25_index.pkl', 'rb') as f:
            bm25_retriever = pickle.load(f)
            bm25_retriever.k = 5
    except FileNotFoundError:
        print("Error: ./bm25_index.pkl not found. Please ensure the path is correct.")
        exit(1)

    print("Configuring Ensemble Retriever...")
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever], 
        weights=[0.5, 0.5]
    )

    print("Connecting to local Ollama instance...")
    # Update base_url if Ollama runs on a different port
    llm = Ollama(model="gemma4:e2b", base_url="http://localhost:11434", num_gpu=0)

    # Strict Persona Prompt
    system_prompt = (
        "คุณคือทนายความที่ปรึกษาด้านกฎหมายหมิ่นประมาทของไทย คุณมีนิสัยเป็นมิตร ใจดี และเชี่ยวชาญการอธิบายกฎหมายให้คนทั่วไปเข้าใจได้ง่าย ชื่อจ๋า เป็นผู้หญิง\n"
        "หน้าที่ของคุณคือให้คำปรึกษาจากข้อมูลกฎหมายและคำพิพากษาศาลฎีกา (Context) ที่ได้รับมาเท่านั้น\n\n"
        
        "กฎการตอบ (ต้องทำตามอย่างเคร่งครัด):\n"
        "1. ฟันธงความผิด: เริ่มต้นประโยคด้วยการสรุปให้ชัดเจนว่า 'น่าจะเข้าข่ายความผิดค่ะ', 'ไม่น่าจะเข้าข่ายความผิดค่ะ', หรือ 'กรณีนี้ก้ำกึ่งค่ะ' \n"
        "   - ทริคการเทียบเคียง: หากคำด่าของผู้ใช้ไม่ได้ตรงกับใน Context เป๊ะๆ แต่มีรากศัพท์ หรือบริบทความหมายไปในทางเดียวกัน (เช่น ใน Context มีคำว่า 'กะหรี่' หรือ 'ดอกทอง' ส่วนผู้ใช้ถามคำว่า 'อีกะหรี่...', 'อีดอก', 'กระหรี่') ให้นำฎีกานั้นมาเทียบเคียงและตอบได้เลย ไม่ต้องปฏิเสธการตอบ\n"
        "2. ให้เหตุผลและอ้างอิง: ระบุเลขมาตรา และ เลขคำพิพากษาศาลฎีกา (ที่ปรากฏใน Context) เพื่อเป็นหลักฐานสนับสนุน\n"
        "3. อธิบายให้เข้าใจง่าย: เล่าสรุปเนื้อหาของกฎหมายหรือฎีกานั้น ว่าทำไมศาลถึงมองว่าผิดหรือไม่ผิด หรือศาลตีความคำนี้ว่าอย่างไร โดยใช้ภาษาพูดที่คนธรรมดาอ่านแล้วเข้าใจทันที ไม่ต้องคัดลอกภาษากฎหมายมาทั้งดุ้น\n"
        "4. กรณีไม่มีข้อมูลจริงๆ: หากใน Context ไม่มีเนื้อหาที่พอจะเทียบเคียงได้เลยจริงๆ ห้ามแต่งข้อมูลขึ้นมาเองเด็ดขาด ให้ตอบอย่างสุภาพและเป็นมิตรว่า:\n"
        "   'หมอความต้องขออภัยด้วยนะคะ จากฐานข้อมูลฎีกาและข้อกฎหมายที่ฉันมีอยู่ตอนนี้ ยังไม่มีกรณีศึกษาที่ตรงหรือใกล้เคียงกับคำนี้เลยค่ะ เลยอาจจะยังฟันธงทางกฎหมายให้ชัดเจนไม่ได้ค่ะ'\n\n"
        
        "ข้อมูลอ้างอิง (Context):\n{context}"
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "คำถามจากผู้ใช้: {input}")
    ])

    document_chain = create_stuff_documents_chain(llm, prompt_template)
    retrieval_chain = create_retrieval_chain(ensemble_retriever, document_chain)
    
    return retrieval_chain

# --- 2. Interface Implementations ---

def run_cli(qa_chain):
    """Runs the chatbot in the terminal."""
    print("\n" + "="*50)
    print("Thai Defamation Legal Bot (CLI Mode) Started.")
    print("Type 'exit' or 'quit' to stop.")
    print("="*50 + "\n")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down CLI...")
            break
        
        if not user_input.strip():
            continue

        print("Searching legal database and generating response...")
        # Using synchronous invoke for CLI
        response = qa_chain.invoke({"input": user_input})
        print(f"\nLawyer Bot: {response['answer']}\n")


async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming messages from Telegram."""
    user_input = update.message.text
    qa_chain = context.bot_data['qa_chain']

    # Send a typing action to let the user know the bot is processing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        # Using asynchronous ainvoke so it doesn't block the Telegram event loop
        response = await qa_chain.ainvoke({"input": user_input})
        answer = response['answer']
    except Exception as e:
        answer = "An error occurred while processing your request locally."
        print(f"Error during generation: {e}")

    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


async def start_telegram_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command in Telegram."""
    welcome_text = (
        "สวัสดีครับ I am a legal consultant bot specializing in Thai defamation law. "
        "Please describe your situation or the specific phrases used, and I will check the Supreme Court judgments."
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text)


def run_telegram(qa_chain, token: str):
    """Initializes and runs the Telegram bot."""
    print("Starting Telegram Bot...")
    app = ApplicationBuilder().token(token).build()

    # Pass the chain into bot_data so handlers can access it
    app.bot_data['qa_chain'] = qa_chain

    app.add_handler(CommandHandler("start", start_telegram_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))

    print("Telegram Bot is polling. Press Ctrl+C to stop.")
    app.run_polling()

# --- 3. Main Execution Block ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Hybrid RAG Thai Defamation Bot.")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["cli", "telegram"], 
        default="cli",
        help="Choose the interface mode: 'cli' or 'telegram'."
    )
    parser.add_argument(
        "--token", 
        type=str, 
        help="Telegram Bot Token (Required if mode is 'telegram')."
    )

    args = parser.parse_args()

    # Initialize the core logic regardless of the mode
    print("Initializing Core RAG System. This may take a moment...")
    rag_chain = setup_rag_chain()

    if args.mode == "cli":
        run_cli(rag_chain)
    elif args.mode == "telegram":
        if not args.token:
            # Try to grab from environment if not passed as an argument
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            if not token:
                print("Error: Telegram mode requires a bot token. Provide it via --token or TELEGRAM_BOT_TOKEN environment variable.")
                sys.exit(1)
        else:
            token = args.token
            
        run_telegram(rag_chain, token)