"""
URL configuration for jijian project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from task import duty, views, file_handle

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('api/tasks/', duty.task_list, name='task_list'),
    path('api/tasks/create/', duty.create_task, name='create_task'),
    path('api/tasks/<int:task_id>/edit/', duty.edit_task, name='edit_task'),
    path('api/tasks/<int:task_id>/delete/', duty.delete_task, name='delete_task'),
    path('api/process_save/', file_handle.process_save, name='process_save'),
    path('api/process_progress/<str:task_id>/', file_handle.process_progress, name='process_progress'),
]
