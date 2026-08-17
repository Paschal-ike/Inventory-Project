from django.urls import path

from projects import views

app_name = "projects"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("projects/", views.project_list, name="project_list"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/members/add/", views.project_add_member, name="project_add_member"),
    path("projects/<int:pk>/members/<int:user_id>/remove/", views.project_remove_member, name="project_remove_member"),
    path("projects/<int:pk>/cost-codes/new/", views.cost_code_create, name="cost_code_create"),
]
