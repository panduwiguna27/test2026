from django.urls import path

from scheduler_app import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/run-pending/', views.run_pending_tasks, name='run_pending_tasks'),
]
