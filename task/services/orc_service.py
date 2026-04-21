
import warnings
import sys
import subprocess
import os



# ===================== 核心功能 =====================
import requests
from pathlib import Path
from PIL import Image




class TextExtractor:
    def _get_file_ext(self, file_path: str) -> str:
        return Path(file_path).suffix.lower()

    def _extract_docx(self, file_path: str) -> str:
        try:
            # import docx
            # doc = docx.Document(file_path)
            # return "\n".join([para.text for para in doc.paragraphs])
            return "docx 暂不支持"
        except Exception as e:
            return f"docx提取失败：{str(e)}"
        

    def _extract_doc(self, file_path: str) -> str:
        try:
            
            text = textract.process(file_path)
            return text.decode("utf-8", errors="ignore")
        except Exception as e:
            return f"doc提取失败：{str(e)}"

    def _extract_pdf(self, file_path: str) -> str:
        # text = ""
        # try:
        #     with pdfplumber.open(file_path) as pdf:
        #         for page in pdf.pages:
        #             page_text = page.extract_text()
        #             if page_text:
        #                 text += page_text + "\n"
        #     return text.strip()
        # except Exception as e:
        #     return f"PDF提取失败：{str(e)}"
        return "PDF 暂不支持"

    def _extract_image(self, file_path: str) -> str:
        try:
            url = "https://api.ocr.space/parse/image"
            with open(file_path, "rb") as f:
                data = {"apikey": "K89891556288957", "language": "chs"}
                files = {"file": f}
                res = requests.post(url, data=data, files=files, timeout=30)
            result = res.json()
            if result.get("IsErroredOnProcessing"):
                return "图片识别失败"
            return "\n".join([item["ParsedText"] for item in result["ParsedResults"]]).strip()
        except Exception as e:
            return f"图片OCR失败：{str(e)}"

    def extract_text(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return "错误：文件不存在！"
        ext = self._get_file_ext(file_path)
        if ext == ".doc":
            return self._extract_doc(file_path)
        elif ext == ".docx":
            return self._extract_docx(file_path)
        elif ext == ".pdf":
            return self._extract_pdf(file_path)
        elif ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            return self._extract_image(file_path)
        else:
            return f"不支持格式：{ext}"


# ===================== 使用 =====================
if __name__ == "__main__":
    extractor = TextExtractor()
    file_path = r"C:\Users\Administrator\Desktop\2d49baa1cd11728b9d28123c8efcc3cec3fd2c75.jpeg"

    print("📄 提取结果")
    print("=" * 60)
    print(extractor.extract_text(file_path))