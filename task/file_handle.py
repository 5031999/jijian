import os
import time
import zipfile
import json
import threading
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
from .models import TaskFile

# 全局进度存储
progress_store = {}

BASE_SAVE_DIR = r"D:\2222"


# =========================
# OCR（占位）
# =========================
class TextExtractor:
    def extract_text(self, file_path):
        return f"【模拟文本】来自文件: {os.path.basename(file_path)}"


# =========================
# SSE 进度监听接口
# =========================
@csrf_exempt
def process_progress(request, task_id):
    """SSE接口：监听处理进度"""
    def generate_progress():
        last_progress = []

        while True:
            if task_id in progress_store:
                current_progress = progress_store[task_id]
                # 只发送新增的进度消息
                new_messages = current_progress[len(last_progress):]
                for message in new_messages:
                    yield f"data: {json.dumps(message)}\n\n"

                last_progress = current_progress.copy()

                # 如果处理完成，结束SSE
                if any(msg.get('type') in ['complete', 'error'] for msg in current_progress):
                    break

            time.sleep(1)  # 每秒检查一次进度

    response = StreamingHttpResponse(
        generate_progress(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Cache-Control'
    return response


# =========================
# ⭐ 核心接口 - 启动后台处理
# =========================
@csrf_exempt
def process_save(request):
    if request.method != "POST":
        return JsonResponse({"code": 1, "msg": "只支持POST"})

    zip_file = request.FILES.get("zip_file")
    task_id = request.POST.get("task_id")

    if not zip_file:
        return JsonResponse({"code": 1, "msg": "没有上传压缩包"})

    if not task_id:
        return JsonResponse({"code": 1, "msg": "缺少task_id"})

    # 初始化进度存储
    progress_store[task_id] = []

    # 在主线程中读取文件内容，避免后台线程访问已关闭的文件
    zip_content = b''
    for chunk in zip_file.chunks():
        zip_content += chunk

    def send_progress(message):
        """发送进度消息"""
        progress_store[task_id].append(message)

    # 启动后台处理线程
    def background_process(zip_data):
        try:
            send_progress({'type': 'start', 'message': '开始处理压缩包...'})

            # 1️⃣ 创建时间戳目录
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_root = os.path.join(BASE_SAVE_DIR, timestamp)
            os.makedirs(save_root, exist_ok=True)

            send_progress({'type': 'progress', 'message': f'创建保存目录: {save_root}'})

            # 2️⃣ 解压zip文件到时间戳目录
            zip_path = os.path.join(save_root, "temp.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_data)

            send_progress({'type': 'progress', 'message': '正在解压压缩包...'})

            # 解压到时间戳目录
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(save_root)

            # 删除临时zip文件
            os.remove(zip_path)

            send_progress({'type': 'progress', 'message': '解压完成，开始分析文件结构...'})

            # 找到解压后的根目录
            extracted_items = os.listdir(save_root)
            if not extracted_items:
                send_progress({'type': 'error', 'message': '压缩包为空'})
                return

            # 如果只有一个根目录，取它；否则整个save_root作为根目录
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(save_root, extracted_items[0])):
                upload_root = os.path.join(save_root, extracted_items[0])
            else:
                upload_root = save_root

            root_folder = os.path.basename(upload_root)
            send_progress({'type': 'progress', 'message': f'找到根目录: {root_folder}'})

            # 3️⃣ 处理解压后的目录
            extractor = TextExtractor()
            send_progress({'type': 'progress', 'message': '开始处理文件...'})

            # 递归处理并发送进度
            processed_files = process_folder_with_progress(upload_root, extractor, send_progress)

            # 发送每个处理完成的文件信息
            for file_info in processed_files:
                send_progress({'type': 'file_processed', 'file': file_info})

            send_progress({'type': 'progress', 'message': '所有文件处理完成，开始执行最终处理...'})

            # 更新数据库
            try:
                task_id_int = int(task_id)
                task = TaskFile.objects.get(id=task_id_int)
                task.result_json = save_root
                task.status = "completed"
                task.save()
                send_progress({'type': 'progress', 'message': f'数据库更新成功: 任务 {task_id_int} 状态更新为 completed'})
            except Exception as e:
                send_progress({'type': 'error', 'message': f'数据库更新失败: {e}'})

            # 发送完成消息
            send_progress({'type': 'complete', 'data': [{'file_name': root_folder, 'save_path': upload_root, 'summary': '解压完成 + 文档提取 + 图片转PDF 已完成'}]})

        except Exception as e:
            send_progress({'type': 'error', 'message': str(e)})

    # 启动后台线程
    thread = threading.Thread(target=background_process, args=(zip_content,))
    thread.daemon = True
    thread.start()

    return JsonResponse({"code": 0, "msg": "处理已启动", "task_id": task_id})


# =========================
# 📁 递归处理目录 - 带进度
# =========================
def process_folder_with_progress(current_path, extractor, send_progress):
    processed_files = []
    image_files = []

    for item in os.listdir(current_path):
        full_path = os.path.join(current_path, item)

        # 子目录递归
        if os.path.isdir(full_path):
            sub_processed = process_folder_with_progress(full_path, extractor, send_progress)
            processed_files.extend(sub_processed)
            continue

        ext = os.path.splitext(item)[1].lower()

        # 图片
        if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            image_files.append(full_path)
            processed_files.append({
                'type': 'image',
                'path': full_path,
                'status': '待合成PDF'
            })

        # 文档
        elif ext in [".doc", ".docx", ".pdf"]:
            process_document(full_path, extractor)
            txt_path = os.path.splitext(full_path)[0] + ".txt"
            processed_files.append({
                'type': 'document',
                'path': full_path,
                'output': txt_path,
                'status': '已提取文本'
            })


        # 当前目录图片 → OCR → txt
        if image_files:
            # ⭐ 按创建时间排序
            image_files.sort(key=lambda x: os.path.getctime(x))

            all_text = []

            for img_path in image_files:
                try:
                    text = extractor.extract_text(img_path)

                    all_text.append(f"\n===== {os.path.basename(img_path)} =====\n")
                    all_text.append(text)

                    send_progress({
                        'type': 'progress',
                        'message': f'OCR完成: {os.path.basename(img_path)}'
                    })

                except Exception as e:
                    print("OCR失败:", img_path, e)

            # ⭐ 写入txt
            txt_path = os.path.join(current_path, "images_ocr.txt")

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(all_text))

            processed_files.append({
                'type': 'image_ocr',
                'path': txt_path,
                'status': '图片OCR完成',
                'images_count': len(image_files)
            })

    return processed_files


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
            "PDF",
            save_all=True,
            append_images=images[1:]
        )

        return pdf_path

    except Exception as e:
        print("PDF生成失败:", e)
        return None