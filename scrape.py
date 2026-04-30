import requests
from bs4 import BeautifulSoup
import csv
import time
import re

def clean_text(text):
    """ลบ Enter ซ่อนฟันหนู และทำความสะอาดช่องว่าง เพื่อล็อกให้ CSV อยู่ใน 1 แถวเป๊ะๆ"""
    if not text: return ""
    text = str(text).replace('"', "'") 
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_print_item(container, class_name, remove_labels=None):
    """ฟังก์ชันเจาะลึกเข้าไปดึงเนื้อหาจากแท็กเฉพาะของรูปแบบหน้าพิมพ์"""
    node = container.find('li', class_=re.compile(class_name))
    if not node: return ""
    
    text = node.get_text(separator=' ', strip=True)
    if remove_labels:
        for label in remove_labels:
            text = text.replace(label, '').strip()
            
    return clean_text(text)

def scrape_deka():
    search_url = "https://deka.supremecourt.or.th/search"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    with open('supremecourt_rag_data.csv', mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['deka_id', 'deka_no', 'keyword', 'litigant', 'law', 'judge', 'source', 'short_summary', 'long_summary', 'full_text'])
        
        # ทดสอบที่หน้า 1 ถึง 3
        for page in range(1, 80): 
            print(f"\n*** Scraping Search Page {page} ***")
            payload = {
                'search_word': 'หมิ่นประมาท',
                'search_form_type': 'basic',
                'count_result': '1575',
                'count_all_result': '133103',
                'total_page': '79',
                'start': 'false',
                'default': 'false',
                'page': str(page) 
            }
            
            try:
                page_url = f"{search_url}/index/{page}" if page > 1 else search_url
                response = requests.post(page_url, data=payload, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                print_buttons = soup.find_all('button', id=lambda x: x and x.startswith('btn_print_'))
                print(f"Found {len(print_buttons)} judgments on this page.")
                
                for button in print_buttons:
                    deka_id = button.get('id').replace('btn_print_', '').strip()
                    
                    try:
                        # 1. แงะเอา ID ของกล่องข้อความพิมพ์ที่ซ่อนอยู่ (เช่น vs_723553_2568_content)
                        onclick_val = button.get('onclick', '')
                        match = re.search(r"printdeka\('[^']+',\s*'#([^']+)'", onclick_val)
                        if not match: continue
                        
                        content_id = match.group(1)
                        
                        # 2. หากล่องเนื้อหานั้นในหน้าค้นหาเลย ไม่ต้องโหลดหน้าใหม่!
                        container = soup.find('ul', id=content_id)
                        if not container: continue
                        
                        # 3. สกัดข้อมูลตาม Class ของรูปแบบหน้าพิมพ์
                        deka_no = extract_print_item(container, 'print_item_deka_no', ['คำพิพากษาศาลฎีกาที่'])
                        litigant = extract_print_item(container, 'print_item_litigant')
                        law = extract_print_item(container, 'print_item_law')
                        judge = extract_print_item(container, 'print_item_judge')
                        
                        # รวมศาลชั้นต้นและแหล่งที่มาเข้าด้วยกัน
                        src1 = extract_print_item(container, 'print_item_primarycourt')
                        src2 = extract_print_item(container, 'print_item_source', ['แหล่งที่มา'])
                        source = clean_text(f"{src1} {src2}")
                        
                        short_summary = extract_print_item(container, 'print_item_short_text')
                        long_summary = extract_print_item(container, 'print_item_long_text')
                        
                        # จัดแพตเทิร์น Full Text เพื่อใช้เข้า RAG
                        full_text = clean_text(f"ย่อสั้น: {short_summary} || ย่อยาว: {long_summary}")
                        
                        writer.writerow([
                            deka_id, deka_no, 'หมิ่นประมาท', litigant, law, judge, source, short_summary, long_summary, full_text
                        ])
                        
                        print(f"  [+] Success: ID {deka_id} -> No. {deka_no}")
                        
                    except Exception as e:
                        print(f"  [-] Error ID {deka_id}: {e}")
                        
            except Exception as e:
                print(f"Error on page {page}: {e}")
                
            time.sleep(1)

    print("\nScraping complete! Check supremecourt_rag_data.csv")

if __name__ == "__main__":
    scrape_deka()