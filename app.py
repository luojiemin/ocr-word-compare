import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# 用 ocr.space API 识别图中文字
def extract_word_pairs_ocrspace(image_bytes):
    api_key = 'helloworld'
    url = 'https://api.ocr.space/parse/image'
    
    response = requests.post(
        url,
        files={"filename": image_bytes},
        data={
            "apikey": api_key,
            "language": "chs",
            "isOverlayRequired": False
        }
    )
    
    result = response.json()
    text = result["ParsedResults"][0]["ParsedText"] if "ParsedResults" in result else ""
    
    lines = text.split('\n')
    word_defs = []
    for line in lines:
        match = re.match(r'[*•]?\s*([a-zA-Z\s]+)[^\u4e00-\u9fa5a-zA-Z]+([\u4e00-\u9fa5；;，,]+)', line.strip())
        if match:
            word = re.sub(r'\s+', ' ', match.group(1).strip().lower())
            meaning = re.split(r'[；;，,]', match.group(2).strip())
            meaning = [m for m in meaning if m]
            if word and meaning:
                meaning_str = '；'.join(meaning[:2])
                if all(x not in word for x in ['=', '/', '“', '”', '(', ')']):
                    word_defs.append({'单词': word, '释义': meaning_str})
    return word_defs

# 抓取有道释义
def query_youdao(word):
    url = f"https://www.youdao.com/result?word={word}&lang=en"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        trans = soup.select('.trans-container ul li')
        meanings = [li.text.strip() for li in trans]
        return '；'.join(meanings[:2]) if meanings else '无释义'
    except:
        return '抓取失败'

# Streamlit 界面
st.title("📘 英文单词图片识别 + 有道释义比对系统")

uploaded_files = st.file_uploader("上传多张词汇图像（支持 jpg/png）", type=["jpg", "png"], accept_multiple_files=True)

if uploaded_files:
    all_entries = []
    for file in uploaded_files:
        st.image(file, caption=file.name, width=200)
        entries = extract_word_pairs_ocrspace(file)
        for entry in entries:
            entry['有道释义'] = query_youdao(entry['单词'])
            entry['是否一致'] = '是' if entry['释义'] in entry['有道释义'] else '否'
        all_entries.extend(entries)

    if all_entries:
        df = pd.DataFrame(all_entries)
        st.dataframe(df)

        st.download_button(
            label="📥 下载 Excel",
            data=df.to_excel(index=False, engine='openpyxl'),
            file_name="识别结果比对.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
