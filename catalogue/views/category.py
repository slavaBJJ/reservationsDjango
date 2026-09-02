from django.shortcuts import  get_object_or_404,render

from catalogue.models import Category

def index(request):
    categories = Category.objects.prefetch_related('shows').order_by('name')

    return render(request,
                  'category/index.html',
                  {'categories': categories},
                  )

def show(request, category_slug):
    category = get_object_or_404(
        Category.objects.prefetch_related('shows'),
        slug = category_slug,
    )

    return render(
        request,
        'category/show.html',
        {'category': category},
    )