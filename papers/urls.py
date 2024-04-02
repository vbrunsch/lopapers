from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.list_papers, name='list_papers'),
    path('create_group/', views.create_group, name='create_group'),
    path('set_operation/', views.perform_set_operation, name='perform_set_operation'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='papers/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='papers/logout.html'), name='logout'),
    path('paper_detail_ajax/<int:pk>/', views.paper_detail_ajax, name='paper_detail_ajax'),
    path('create_group_selection/', views.create_group_from_selection, name='create_group_from_selection'),
    path('perform_set_operation_and_display/', views.perform_set_operation_and_display, name='perform_set_operation_and_display'),
    path('manage_groups/', views.manage_groups, name='manage_groups'),
    path('delete_groups/', views.delete_groups, name='delete_groups'),
    path('search/', views.search_papers, name='search_papers'),
    path('lda_clustering/', views.lda_clustering, name='lda_clustering'),
    path('perform_lda_clustering/', views.perform_lda_clustering, name='perform_lda_clustering'),
    path('lda_visualization/', views.lda_visualization, name='lda_visualization'),




]



