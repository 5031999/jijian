from django.shortcuts import render


def index(request):
    return render(request, 'index.html')


def upload(request):
    task_id = request.GET.get('task_id')
    return render(request, 'upload.html', {'task_id': task_id})
