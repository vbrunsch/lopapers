from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required  
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.conf import settings
from .models import Paper, Group, LdaModel, Topic
from .forms import GroupForm, SetOperationForm, UserRegisterForm
from .utils import run_lda_clustering

def lda_visualization(request):
    file_url = settings.MEDIA_URL + 'lda_visualization.html'
    return redirect(file_url)

def lda_clustering(request):
    # This assumes you have a model called LdaModel that stores your LDA results
    # And each Paper object has a foreign key to a Topic object, which in turn is linked to LdaModel
    lda_results = LdaModel.objects.latest('date_created')  # Get the latest LDA model results
    topics = lda_results.topics.all()  # Assuming LdaModel has a relation to topics
    
    # Assuming you want to display papers for the first topic by default
    default_topic_id = topics.first().id if topics.exists() else None
    selected_topic_id = request.GET.get('topic_id', default_topic_id)
    
    if selected_topic_id:
        selected_topic = topics.get(id=selected_topic_id)
        papers = selected_topic.papers.all()  # Assuming a Topic model has a relation to papers
    else:
        papers = Paper.objects.none()
    
    context = {
        'lda_results': lda_results,
        'topics': topics,
        'selected_topic_id': selected_topic_id,
        'papers': papers,
    }
    return render(request, 'papers/lda_clustering.html', context)

@require_POST  # Ensure this view only accepts POST requests
def perform_lda_clustering(request):
    # Clear existing topics
    Topic.objects.all().delete()
    # Trigger the LDA clustering process
    run_lda_clustering()

    # If clustering is successful:
    request.session['clustering_performed'] = True

    # Redirect to a page where the user can view the clustering results
    # For simplicity, you might initially redirect back to the main page
    # Later, you can adjust this to redirect to a specific page for viewing clustering results
    return redirect('list_papers')

def parse_query(query_string):
    # This is a very basic parser.
    if "AND" in query_string:
        keywords = query_string.split("AND")
        return [Q(title__icontains=keyword.strip()) for keyword in keywords], 'AND'
    elif "OR" in query_string:
        keywords = query_string.split("OR")
        return [Q(title__icontains=keyword.strip()) for keyword in keywords], 'OR'
    else:
        return [Q(title__icontains=query_string.strip())], 'AND'

def search_papers(query, base_queryset):
    query_terms = query.split()
    q_objects = Q()

    for term in query_terms:
        if term.upper() == 'OR':
            continue  # Skip 'OR' for now, handle in combination logic
        elif term.upper() == 'AND':
            continue  # Skip 'AND' for now, handle in combination logic
        else:
            q_objects |= Q(title__icontains=term)  # Default to OR logic

    # Implement basic AND/OR logic
    if ' AND ' in query:
        q_objects = Q()
        for term in query.split(' AND '):
            q_objects &= Q(title__icontains=term)
    elif ' OR ' in query:
        q_objects = Q()
        for term in query.split(' OR '):
            q_objects |= Q(title__icontains=term)

    return base_queryset.filter(q_objects)

def paper_detail_ajax(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    paper_data = {
        'title': paper.title,
        'year': paper.year,
        'authors': paper.authors,  # assuming these fields exist
        'abstract': paper.abstract,
        # include other fields you want to display
    }
    return JsonResponse(paper_data)

def list_papers(request):
    
    clustering_performed = request.session.get('clustering_performed', False)
    # Reset the flag to hide the dropdown upon page refresh/navigation
    # request.session['clustering_performed'] = False

    # Initialize the form and result set
    form = SetOperationForm(request.POST or None)
    result_set = None

    # Extract query parameters
    query = request.GET.get('query')
    group_id = request.GET.get('group_selection')
    year = request.GET.get('year')
    keyword = request.GET.get('keyword')

    if 'perform_lda' in request.POST:
        # Here you would call your function to perform LDA clustering
        # For example, run_lda_clustering()
        # Ensure this function updates the database with the new clustering results
        run_lda_clustering()

    topics = Topic.objects.all() if clustering_performed else Topic.objects.none()
    selected_topic_id = request.GET.get('topic_id', None)

    if form.is_valid():
        # Perform set operation based on the operation type
        operation = form.cleaned_data['operation']
        group1 = form.cleaned_data['group1']
        group2 = form.cleaned_data['group2']

        if operation == 'union':
            result_set = (group1.papers.all() | group2.papers.all()).distinct()
        elif operation == 'intersection':
            result_set = group1.papers.all() & group2.papers.all()
        elif operation == 'difference':
            result_set = group1.papers.all().difference(group2.papers.all())
        else:
            result_set = Paper.objects.none()

    # Start with a base QuerySet
    papers = Paper.objects.all()

    if selected_topic_id:
        selected_topic = Topic.objects.get(id=selected_topic_id)
        papers = selected_topic.papers.all()  # Assuming a ForeignKey from Paper to Topic

    # If a group is selected, narrow down papers to that group
    if group_id and group_id != 'all':
        group = Group.objects.get(id=group_id)
        papers = group.papers.all()

    # If there's a query, apply it
    if query:
        papers = search_papers(query, papers)

    # Apply year and keyword filters
    if year:
        papers = papers.filter(year=year)
    if keyword:
        papers = papers.filter(title__icontains=keyword)

    # If a set operation was performed, use that result set
    if result_set is not None:
        papers = result_set

    # Prepare the context for rendering
    groups = Group.objects.all()
    return render(request, 'papers/list_papers.html', {
        'papers': papers,
        'set_operation_form': form,  # Pass the form for set operations
        'groups': groups,
        'current_group_id': group_id,
        'topics': topics,
        'clustering_performed': clustering_performed,
        'selected_topic_id': selected_topic_id,
    })


#def list_papers(request):
#    papers = Paper.objects.all()
#    return render(request, 'papers/list_papers.html', {'papers': papers})

from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Paper, Group

from django.http import JsonResponse

import logging
logger = logging.getLogger('soop')

@login_required
def create_group_from_selection(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        paper_ids = request.POST.getlist('paper_ids')
        logger.info(f"Creating group: {group_name} with papers: {paper_ids}")
        if group_name and paper_ids:
            try:
                new_group = Group.objects.create(name=group_name, owner=request.user)
                for paper_id in paper_ids:
                    paper = Paper.objects.get(id=paper_id)
                    new_group.papers.add(paper)
                new_group.save()
                logger.info(f"Group {group_name} created successfully.")
                return JsonResponse({"success": True, "groupName": group_name, "groupId": new_group.id})
            except Exception as e:
                logger.error(f"Failed to create group: {e}")
                return JsonResponse({"success": False, "error": str(e)})
        else:
            return JsonResponse({"success": False, "error": "Missing group name or paper IDs."})
    return JsonResponse({"success": False, "error": "Invalid request"})

    
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_papers')
    else:
        form = GroupForm()
    return render(request, 'papers/create_group.html', {'form': form})

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

@login_required
def perform_set_operation_and_display(request):
    if request.method == 'POST':
        form = SetOperationForm(request.POST)
        if form.is_valid():
            operation = form.cleaned_data['operation']
            group1 = form.cleaned_data['group1']
            group2 = form.cleaned_data['group2']

            papers1 = group1.papers.all()
            papers2 = group2.papers.all()

            if operation == 'union':
                result_set = papers1 | papers2
            elif operation == 'intersection':
                result_set = papers1 & papers2
            elif operation == 'difference':
                result_set = papers1.difference(papers2)
            else:
                result_set = Paper.objects.none()

            
        # No need to create a new group or return JSON, directly render the template with results
        return render(request, 'papers/list_papers.html', {
            'papers': result_set,  # Use 'papers' to align with your list_papers template structure
            # Include other necessary context like 'groups' if needed
            #'groups': Group.objects.all(),
        })
    
def perform_set_operation(request):
    if request.method == 'POST':
        form = SetOperationForm(request.POST)
        logger.debug("Performing set operation")
        if form.is_valid():
            operation = form.cleaned_data['operation']
            group1 = form.cleaned_data['group1']
            group2 = form.cleaned_data['group2']

            logger.debug(f"Operation: {operation}, Group1: {group1.id}, Group2: {group2.id}")
            
            # Retrieve the Paper QuerySets from the selected groups
            papers1 = group1.papers.all()
            papers2 = group2.papers.all()

            # Perform the set operation
            if operation == 'union':
                result_set = papers1 | papers2
            elif operation == 'intersection':
                result_set = papers1 & papers2
            elif operation == 'difference':
                result_set = papers1.difference(papers2)
            else:
                result_set = Paper.objects.none()

            # For AJAX requests, return JSON data
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                result_data = list(result_set.values('id', 'title', 'year'))
                logger.debug(f"Returning JSON response with result_set: {result_data}")
                return JsonResponse({'result_set': result_data})
            else:
                # For non-AJAX requests (optional, depending on your needs)
                logger.debug("Non-AJAX request received")
                return render(request, 'papers/set_operation_result.html', {'result_set': result_set})
        else:
            # Log form errors
            logger.error(f"Form errors: {form.errors}")

    else:
        form = SetOperationForm()

    return render(request, 'papers/perform_set_operation.html', {'form': form})

def manage_groups(request):
    groups = Group.objects.all()
    return render(request, 'papers/manage_groups.html', {'groups': groups})

@login_required
@require_POST
def delete_groups(request):
    group_ids = request.POST.getlist('group_ids')
    Group.objects.filter(id__in=group_ids).delete()
    # Redirect to the manage groups page or wherever appropriate
    return redirect('manage_groups')
