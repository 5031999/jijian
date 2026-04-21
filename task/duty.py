import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TaskFile


# =========================
# 1. 获取任务列表（按创建时间倒序）
# =========================
def task_list(request):
    if request.method != "GET":
        return JsonResponse({"code": 1, "msg": "只支持 GET 请求"}, status=405)

    tasks = TaskFile.objects.order_by("-created_at").values(
        "id", "task_name", "file_name", "file_path", "status", "created_at"
    )

    data = [
        {
            "id": t["id"],
            "task_name": t["task_name"],
            "file_name": t["file_name"],
            "file_path": t["file_path"],
            "status": t["status"],
            "created_at": t["created_at"].strftime("%Y-%m-%d %H:%M:%S") if t["created_at"] else None,
        }
        for t in tasks
    ]

    return JsonResponse({"code": 0, "data": data})


# =========================
# 2. 新建任务
# =========================
@csrf_exempt
def create_task(request):
    if request.method != "POST":
        return JsonResponse({"code": 1, "msg": "只支持 POST 请求"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"code": 1, "msg": "请求体必须为 JSON"}, status=400)

    task_name = body.get("task_name")
    file_path = body.get("file_path")

    if not task_name or not file_path:
        return JsonResponse({"code": 1, "msg": "任务名称和保存路径为必填项"}, status=400)

    TaskFile.objects.create(
        task_name=task_name,
        file_path=file_path,
        status="pending"
    )

    return JsonResponse({"code": 0, "msg": "创建成功"})


# =========================
# 3. 编辑任务
# =========================
@csrf_exempt
def edit_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"code": 1, "msg": "只支持 POST 请求"}, status=405)

    try:
        task = TaskFile.objects.get(id=task_id)
    except TaskFile.DoesNotExist:
        return JsonResponse({"code": 1, "msg": "任务不存在"}, status=404)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"code": 1, "msg": "请求体必须为 JSON"}, status=400)

    task_name = body.get("task_name")
    file_path = body.get("file_path")

    if not task_name or not file_path:
        return JsonResponse({"code": 1, "msg": "任务名称和保存路径为必填项"}, status=400)

    task.task_name = task_name
    task.file_path = file_path
    task.save()

    return JsonResponse({"code": 0, "msg": "编辑成功"})


# =========================
# 4. 删除任务
# =========================
@csrf_exempt
def delete_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"code": 1, "msg": "只支持 POST 请求"}, status=405)

    try:
        task = TaskFile.objects.get(id=task_id)
        task.delete()
        return JsonResponse({"code": 0, "msg": "删除成功"})
    except TaskFile.DoesNotExist:
        return JsonResponse({"code": 1, "msg": "任务不存在"}, status=404)
