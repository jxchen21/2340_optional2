from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CustomErrorList
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')
def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html',
            {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username = request.POST['username'],
            password = request.POST['password']
        )
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html',
                {'template_data': template_data})
        else:
            auth_login(request, user)
            return redirect('home.index')
def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html',
            {'template_data': template_data})
    elif request.method == 'POST':
        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            form.save()
            return redirect('accounts.login')
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html',
                {'template_data': template_data})

@login_required
def admin_dashboard(request):
    """Admin dashboard to view all user accounts"""
    # Check if user is admin (staff or superuser)
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("You do not have permission to access this page.")
    
    template_data = {}
    template_data['title'] = 'Admin Dashboard'
    
    # Get all users (active and inactive)
    all_users = User.objects.all().order_by('-date_joined')
    active_users = User.objects.filter(is_active=True).order_by('-date_joined')
    inactive_users = User.objects.filter(is_active=False).order_by('-date_joined')
    
    # Calculate statistics
    total_users = User.objects.count()
    active_count = active_users.count()
    inactive_count = inactive_users.count()
    staff_count = User.objects.filter(is_staff=True).count()
    superuser_count = User.objects.filter(is_superuser=True).count()
    
    template_data['all_users'] = all_users
    template_data['active_users'] = active_users
    template_data['inactive_users'] = inactive_users
    template_data['total_users'] = total_users
    template_data['active_count'] = active_count
    template_data['inactive_count'] = inactive_count
    template_data['staff_count'] = staff_count
    template_data['superuser_count'] = superuser_count
    
    return render(request, 'accounts/admin_dashboard.html',
                  {'template_data': template_data})

@login_required
def deactivate_user(request, user_id):
    """Deactivate a user account"""
    # Check if user is admin (staff or superuser)
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("You do not have permission to perform this action.")
    
    user_to_deactivate = get_object_or_404(User, id=user_id)
    
    # Prevent deactivating yourself
    if user_to_deactivate.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('accounts.admin_dashboard')
    
    # Prevent deactivating superusers (safety measure)
    if user_to_deactivate.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to deactivate superuser accounts.')
        return redirect('accounts.admin_dashboard')
    
    user_to_deactivate.is_active = False
    user_to_deactivate.save()
    messages.success(request, f'User "{user_to_deactivate.username}" has been deactivated successfully.')
    
    return redirect('accounts.admin_dashboard')

@login_required
def reactivate_user(request, user_id):
    """Reactivate a user account"""
    # Check if user is admin (staff or superuser)
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("You do not have permission to perform this action.")
    
    user_to_reactivate = get_object_or_404(User, id=user_id)
    
    user_to_reactivate.is_active = True
    user_to_reactivate.save()
    messages.success(request, f'User "{user_to_reactivate.username}" has been reactivated successfully.')
    
    return redirect('accounts.admin_dashboard')