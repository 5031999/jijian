import os
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image


BASE_SAVE_DIR = r"D:\2222"


# =========================
# OCR（占位）
# =========================
class TextExtractor:
    def extract_text(self, file_path):
        return f"【模拟文本】来自文件: {os.path.basename(file_path)}"


# =========================
# ⭐ 核心接口
# =========================
@csrf_exempt
def process_save(request):
    if request.method != "POST":
        return JsonResponse({"code": 1, "msg": "只支持POST"})

    files = request.FILES.getlist("files")

    if not files:
        return JsonResponse({"code": 1, "msg": "没有上传文件"})

    try:
        # 1️⃣ 创建时间戳目录
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_root = os.path.join(BASE_SAVE_DIR, timestamp)

        # 2️⃣ 保存文件（还原目录结构）
        for f in files:
            # ⭐⭐⭐ 关键：用 _name 获取完整路径
            rel_path = f._name.replace("\\", "/")

            # 安全处理（防止异常路径）
            rel_path = rel_path.lstrip("/")

            save_path = os.path.join(save_root, rel_path)

            # 创建目录
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 写入文件
            with open(save_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

        # 3️⃣ 处理整个目录（不要再猜 root）
        extractor = TextExtractor()
        process_folder(save_root, extractor)

        return JsonResponse({
            "code": 0,
            "msg": "处理完成",
            "data": [{
                "file_name": "全部文件",
                "save_path": save_root,
                "summary": "目录还原 + 文档提取 + 图片转PDF 已完成"
            }]
        })

    except Exception as e:
        return JsonResponse({"code": 1, "msg": str(e)})


# =========================
# 📁 递归处理目录
# =========================
def process_folder(current_path, extractor):
    image_files = []

    for item in os.listdir(current_path):
        full_path = os.path.join(current_path, item)

        # 子目录递归
        if os.path.isdir(full_path):
            process_folder(full_path, extractor)
            continue

        ext = os.path.splitext(item)[1].lower()

        # 图片
        if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            image_files.append(full_path)

        # 文档
        elif ext in [".doc", ".docx", ".pdf"]:
            process_document(full_path, extractor)

    # 当前目录图片 → PDF
    if image_files:
        create_pdf_from_images(image_files, current_path)


# =========================
# 📄 文档转 txt
# =========================
def process_document(file_path, extractor):
    try:
        text = extractor.extract_text(file_path)

        txt_path = os.path.splitext(file_path)[0] + ".txt"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

    except Exception as e:
        print("文档处理失败:", file_path, e)


# =========================
# 🖼️ 图片转 PDF
# =========================
def create_pdf_from_images(image_files, save_dir):
    try:
        # 按创建时间排序
        image_files.sort(key=lambda x: os.path.getctime(x))

        images = []

        for img_path in image_files:
            try:
                img = Image.open(img_path).convert("RGB")
                images.append(img)
            except Exception as e:
                print("图片读取失败:", img_path, e)

        if not images:
            return

        pdf_path = os.path.join(save_dir, "images.pdf")

        images[0].save(
            pdf_path,
            save_all=True,
            append_images=images[1:]
        )

    except Exception as e:
        print("PDF生成失败:", e)
# import os
# import time
# import tempfile
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .services.orc_service import TextExtractor
# from .services.model_service import ModelClient1
# import json
# from django.http import JsonResponse
# from .models import TaskFile


# BASE_SAVE_DIR = r"D:\2222"
# MAX_WORKERS = 5  # ⚠️ 建议先小一点


# # ======================
# # 工具函数
# # ======================

# def create_batch_dir():
#     timestamp = str(int(time.time()))
#     batch_dir = os.path.join(BASE_SAVE_DIR, timestamp)
#     os.makedirs(batch_dir, exist_ok=True)
#     return batch_dir


# def save_uploaded_file(file, save_dir):
#     """先保存文件（线程外做）"""
#     filename = os.path.basename(file.name)
#     path = os.path.join(save_dir, filename)
#     with open(path, "wb") as f:
#         for chunk in file.chunks():
#             f.write(chunk)

#     return path


# def extract_text(extractor, file_path):
#     return extractor.extract_text(file_path)


# def call_model(text):
#     """⚠️ 线程里只做模型调用"""
#     client = ModelClient1()
#     prompt = "帮我总结下面文本：\n" + text[:2000]
#     return client.chat(prompt)





# def create_task(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST"})

#     data = json.loads(request.body)
#     task_name = data.get("task_name", "未命名任务")

#     task = TaskFile.objects.create(
#         task_name=task_name,
#         status="pending"
#     )

#     return JsonResponse({
#         "task_id": task.id,
#         "task_name": task.task_name
#     })

# # ======================
# # 主接口
# # ======================
# @csrf_exempt
# def process_and_save(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Only POST allowed'})
#     task_id = request.POST.get("task_id")
#     files = request.FILES.getlist('files')
#     if not files:
#         return JsonResponse({'error': '没有上传文件'})

#     extractor = TextExtractor()
#     batch_dir = create_batch_dir()

#     # ======================
#     # ① 先处理文件（主线程）
#     # ======================
#     file_tasks = []

#     for file in files:
#         try:
#             filename = os.path.basename(file.name)
#             folder_name = os.path.splitext(filename)[0]

#             save_dir = os.path.join(batch_dir, folder_name)
#             os.makedirs(save_dir, exist_ok=True)

#             # 保存原文件
#             file_path = save_uploaded_file(file, save_dir)

#             # 提取文本
#             text = extract_text(extractor, file_path)

#             file_tasks.append({
#                 "file_name": filename,
#                 "save_dir": save_dir,
#                 "text": text
#             })

#             print(f"✅ 已提取文本: {filename}")

#         except Exception as e:
#             file_tasks.append({
#                 "file_name": file.name,
#                 "error": str(e)
#             })

#     # ======================
#     # ② 多线程调用模型
#     # ======================
#     results = []

#     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
#         future_map = {}

#         for task in file_tasks:
#             if "error" in task:
#                 results.append(task)
#                 continue

#             future = executor.submit(call_model, task["text"])
#             future_map[future] = task

#         for future in as_completed(future_map):
#             task = future_map[future]

#             try:
#                 summary = future.result(timeout=60)  # ⭐ 防卡死

#                 # 保存 summary
#                 summary_path = os.path.join(task["save_dir"], "summary.txt")
#                 with open(summary_path, "w", encoding="utf-8") as f:
#                     f.write(summary)

#                 results.append({
#                     "file_name": task["file_name"],
#                     "save_path": os.path.abspath(task["save_dir"]),
#                     "summary": summary
#                 })

#                 print(f"🔥 模型完成: {task['file_name']}")

#             except Exception as e:
#                 results.append({
#                     "file_name": task["file_name"],
#                     "error": str(e)
#                 })

#         # 更新数据库
#     if task_id:
#         try:
#             task = TaskFile.objects.get(id=task_id)
#             task.result_json = results
#             task.status = "completed"
#             task.save()
#         except TaskFile.DoesNotExist:
#             pass  # 如果任务不存在，忽略

#     return JsonResponse({
#         "msg": "处理完成（稳定版）",
#         "batch_dir": os.path.abspath(batch_dir),
#         "data": results
#     })

