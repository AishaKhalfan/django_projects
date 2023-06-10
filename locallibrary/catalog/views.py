from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre, Language

# Create your views here.
def index(request):
    """View function for home page of site."""
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_genres = Genre.objects.count()
    num_books_with_the= Book.objects.filter(title__icontains='The').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    context = { #context is a dictionary mapping template variable names to Python objects
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_books_with_the': num_books_with_the,
    } #context is passed to the template engine to be merged with the template file to generate the HTML that is presented to the user.

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)