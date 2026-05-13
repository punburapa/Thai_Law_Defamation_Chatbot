# ⚖️ LAWYER CHATBOT for หมิ่นประมาท (Defamation)

This project introduces "ทนายจ๋า CHATBOT", an intelligent legal assistant specifically designed to provide advice on Thai defamation law (หมิ่นประมาท). Developed as part of CP465 Text Mining, this chatbot aims to simplify access to legal information by leveraging advanced AI techniques.

## 🌟 Problem Definition: หมิ่นประมาท (Defamation)

Defamation is a nuanced area of law that many people are concerned about but often find complex to navigate. Understanding what constitutes defamation and seeking quick, reliable legal guidance can be challenging. This chatbot addresses the need for an accessible tool to clarify such legal questions.

## ✨ Solution: ทนายจ๋า CHATBOT

"ทนายจ๋า CHATBOT" is built to offer clear, concise, and accurate legal advice on defamation. It acts as a friendly and knowledgeable legal consultant, explaining complex legal concepts and case precedents in an easy-to-understand language.

## 🧠 Workflow and Architecture

The chatbot utilizes a **Retrieval Augmented Generation (RAG)** architecture to provide informed responses.

### Components:
-   **User Query:** The user's question, posed via CLI or Telegram.
-   **LLM Model:** **Gemma4:E2B** (running locally) serves as the core language model, generating human-like responses.
-   **Retrieval System:** This system is responsible for fetching relevant legal documents.
    -   **ChromaDB + BM25:** A hybrid retrieval approach combining a vector database (ChromaDB) for semantic search and BM25 for lexical search.
    -   **Langchain:** Orchestrates the RAG pipeline, including an `EnsembleRetriever` to combine results from both ChromaDB and BM25.
-   **Data Sources:**
    -   **ฎีกา (Supreme Court Judgments):** Case precedents provide crucial context for legal interpretations.
    -   **มาตรา (Legal Articles/Sections):** Relevant laws and statutes.
-   **Web Scraping:** **BeautifulSoup** is used to scrape legal documents and judgments.
-   **Text Processing:** **PyThaiNLP** is employed for Thai text processing, including tokenization, which is essential for accurate retrieval and understanding.

The `EnsembleRetriever` with weights `[0.5, 0.5]` balances the contributions from both lexical and semantic search, ensuring comprehensive and relevant information retrieval.

## 🗣️ Chatbot Capabilities and Interaction Guidelines

The chatbot is designed to act as a friendly, kind, and expert legal consultant on Thai defamation law. It adheres to strict response guidelines to ensure clarity and accuracy:

1.  **Conclude Fault (ฟันธงความผิด):** Responses start by clearly stating if an act "น่าจะเข้าข่ายความผิดค่ะ" (likely constitutes an offense), "ไม่น่าจะเข้าข่ายความผิดค่ะ" (unlikely to constitute an offense), or "กรณีนี้ก้ำกึ่งค่ะ" (ambiguous case).
    -   **Comparison Trick:** Even if user's exact words aren't in the context, if they have similar roots or meaning (e.g., "กะหรี่" or "ดอกทอง" for "อี-กะหรี่," "อี-ดอก"), the chatbot will still compare with available judgments.
2.  **Provide Reasons and References (ให้เหตุผลและอ้างอิง):** Responses include specific legal articles and Supreme Court judgments from the provided context as supporting evidence.
3.  **Easy-to-Understand Explanation (อธิบายให้เข้าใจง่าย):** The chatbot summarizes the essence of the law or judgment in simple, everyday language, avoiding overly technical legal jargon.
4.  **Handling Missing Information (กรณีไม่มีข้อมูลจริงๆ):** If the context lacks relevant information, the chatbot will politely state that it cannot provide a clear legal opinion without fabricating information.

## 🚧 Challenges and Future Improvements

During development and local operation, several challenges were identified:
-   **Low Context Window:** Limitations in processing lengthy legal texts.
-   **Slow Performance:** Running larger models locally can be computationally intensive, leading to slow response times.
-   **Model Size Limitations:** Smaller models may not possess the same level of intelligence and nuance as larger counterparts.

Future work could involve exploring more optimized local LLMs, improving context handling, or leveraging cloud-based solutions for better performance and scalability.

## 🛠️ Setup

### 1. Data
Download the necessary data from my [GoogleDrive](https://drive.google.com/drive/folders/1ZZIdGLfIbw2hEILRN9P7pEAgRN-ZT1vg?usp=sharing) and place it in your working directory.

### 2. Create Virtual Environment
```bash
python -m venv env
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Running the Chatbot

**CLI Mode:**
To run the chatbot in command-line interface mode:
```bash
python bot_app.py --mode cli
```

**Telegram Chatbot Mode:**
To run the chatbot as a Telegram bot, you need to create a bot first via [BotFather](https://telegram.me/BotFather) on Telegram to obtain your `[BOT_TOKEN]`.
```bash
python bot_app.py --mode telegram --token [BOT_TOKEN]
```

## 📄 Data Source

The project utilizes Supreme Court Judgments scraped from legal databases and the `pythainlp/thailaw-v1.0` dataset from Hugging Face for the RAG system's retrieval component.

