from django.urls import path
from . import views
urlpatterns = [
    path('signup', views.signup, name='accounts.signup'),
    path('login/', views.login, name='accounts.login'),
    path('logout/', views.logout, name='accounts.logout'),
    path('admin/dashboard/', views.admin_dashboard, name='accounts.admin_dashboard'),
    path('admin/user/<int:user_id>/deactivate/', views.deactivate_user, name='accounts.deactivate_user'),
    path('admin/user/<int:user_id>/reactivate/', views.reactivate_user, name='accounts.reactivate_user'),
]