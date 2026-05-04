
from django.urls import path
from .views import *
urlpatterns = [
    path('user/login/',LoginView.as_view() , name='login'),
    path('user/register/',RegisterView.as_view() , name='Register'),
    path('user/profile/',ProfileView.as_view() , name='Profile'),
    path('user/', UserListView.as_view(), name='user-list'),
    path('user/<int:user_id>/', UserDetailView.as_view()),
    path('user/<int:user_id>/restore/', RestoreUserView.as_view()),
    path('user/<int:user_id>/change-role/', ChangeUserRoleView.as_view()),
    path('user/bulk-delete/', BulkDeleteUserView.as_view()),
    path('user/bulk-restore/', BulkRestoreUserView.as_view()),
    path('dashboard/', DashboardView.as_view()),
]