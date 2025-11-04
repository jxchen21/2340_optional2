from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='recipes.index'),
    path('<int:id>/', views.show, name='recipes.show'),
    path('<int:id>/save/', views.save_recipe, name='recipes.save'),
    path('planner/', views.planner, name='recipes.planner'),
    path('planner/add/', views.add_to_planner, name='recipes.add_to_planner'),
    path('planner/remove/<int:meal_plan_id>/', views.remove_from_planner, name='recipes.remove_from_planner'),
]