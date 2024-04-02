from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required  
from .models import Paper, Group
from .forms import GroupForm, SetOperationForm, UserRegisterForm


def paper_detail(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    return render(request, 'papers/paper_detail.html', {'paper': paper})

def list_papers(request):
    year = request.GET.get('year')
    keyword = request.GET.get('keyword')
    papers = Paper.objects.all()

    if year:
        papers = papers.filter(year=year)
    if keyword:
        papers = papers.filter(title__icontains=keyword)

    return render(request, 'papers/list_papers.html', {'papers': papers})

#def list_papers(request):
#    papers = Paper.objects.all()
#    return render(request, 'papers/list_papers.html', {'papers': papers})

from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Paper, Group

@csrf_exempt
@login_required 
def create_group_from_selection(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        paper_ids = request.POST.getlist('paper_ids')
        papers = Paper.objects.filter(id__in=paper_ids)
        new_group = Group.objects.create(name=group_name, owner=request.user)
        new_group.papers.add(*papers)
        # Show message (You might need to use Django messages framework or JavaScript)
        return redirect('list_papers')  # Redirect back to the papers list or another page

def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_papers')
    else:
        form = GroupForm()
    return render(request, 'papers/create_group.html', {'form': form})

def perform_set_operation(request):
    if request.method == 'POST':
        form = SetOperationForm(request.POST)
        if form.is_valid():
            operation = form.cleaned_data.get('operation')
            
            group1 = form.cleaned_data.get('group1')
            group2 = form.cleaned_data.get('group2')
            
            if operation == 'union':
                result_set = group1.papers.all() | group2.papers.all()
            elif operation == 'intersection':
                result_set = group1.papers.all() & group2.papers.all()
            elif operation == 'difference':
                result_set = group1.papers.all().difference(group2.papers.all())
            else:
                result_set = Paper.objects.none()  # Empty queryset
            
            return render(request, 'papers/set_operation_result.html', {'result_set': result_set})
    else:
        form = SetOperationForm()
    return render(request, 'papers/perform_set_operation.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            # You can add a redirect to login page or home page here
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'papers/register.html', {'form': form})

from django.http import JsonResponse

def perform_set_operation(request):
    if request.method == 'POST':
        form = SetOperationForm(request.POST)
        if form.is_valid():
            operation = form.cleaned_data['operation']
            group1 = form.cleaned_data['group1']
            group2 = form.cleaned_data['group2']
            
            if operation == 'union':
                result_set = group1.papers.all() | group2.papers.all()
            elif operation == 'intersection':
                result_set = group1.papers.all() & group2.papers.all()
            elif operation == 'difference':
                result_set = group1.papers.all().difference(group2.papers.all())
            else:
                result_set = Paper.objects.none()
            
            if request.is_ajax():
                # For AJAX requests, return a JSON response with the papers' titles and years
                result_data = [{'title': paper.title, 'year': paper.year} for paper in result_set]
                return JsonResponse({'result_set': result_data})
            else:
                # For non-AJAX requests, you can keep your existing response
                return render(request, 'papers/set_operation_result.html', {'result_set': result_set})

    else:
        form = SetOperationForm()

    if request.is_ajax():
        # Handle AJAX GET request if needed, for example, to load form initially
        return JsonResponse({'form': 'Your form here or an error message'})

    return render(request, 'papers/perform_set_operation.html', {'form': form})

