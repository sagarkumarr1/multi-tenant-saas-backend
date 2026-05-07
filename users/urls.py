from django.urls import path
from .views import (
    LoginView,
    RegisterView,
    ProfileView,
    UserListView,
    UserDetailView,
    RestoreUserView,
    ChangeUserRoleView,
    BulkDeleteUserView,
    BulkRestoreUserView,
    DashboardView,
)

urlpatterns = [
    path('user/login/',                     LoginView.as_view(),          name='login'),
    path('user/register/',                  RegisterView.as_view(),        name='register'),
    path('user/profile/',                   ProfileView.as_view(),         name='profile'),
    path('user/',                           UserListView.as_view(),        name='user-list'),
    path('user/bulk-delete/',               BulkDeleteUserView.as_view(),  name='bulk-delete'),
    path('user/bulk-restore/',              BulkRestoreUserView.as_view(), name='bulk-restore'),
    path('user/<int:user_id>/',             UserDetailView.as_view(),      name='user-detail'),
    path('user/<int:user_id>/restore/',     RestoreUserView.as_view(),     name='restore-user'),
    path('user/<int:user_id>/change-role/', ChangeUserRoleView.as_view(),  name='change-role'),
    path('dashboard/',                      DashboardView.as_view(),       name='dashboard'),
]
