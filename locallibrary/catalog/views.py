from typing import Any
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from .models import Book, Author, BookInstance, Genre, Language
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
import datetime

from catalog.forms import RenewBookForm

# Create your views here.
def index(request):
    """View function for home page of site."""
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_genres = Genre.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_genres = Genre.objects.count()
    num_books_with_the= Book.objects.filter(title__icontains='The').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = { #context is a dictionary mapping template variable names to Python objects
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_books_with_the': num_books_with_the,
        'num_visits': num_visits,

    } #context is passed to the template engine to be merged with the template file to generate the HTML that is presented to the user.

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    """Generic class-based view for a list of books"""
    model = Book
    context_object_name = 'book_list'   # your own name for the list as a template variable
    #queryset = Book.objects.filter(title__icontains='The')[:5] # Get 5 books containing the title The
    template_name = 'catalog/book_list.html'  # Specify your own template name/location
    paginate_by = 5

    def get_queryset(set):
        return Book.objects.filter(title__icontains='a')[:10]
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BookListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        context['some_data'] = 'This is just some data'
        return context

class BookDetailView(generic.DetailView):
    """Generic class-based detail view for a book"""
    model = Book

    def book_detail_view(request, primary_key):
        try:
            book = Book.objects.get(pk=primary_key)
        except Book.DoesNotExist:
            raise Http404('Book does not exist')

        return render(request, 'catalog/book_detail.html', context={'book': book})
    
class AuthorDetailView(generic.DetailView):
    """Generic class-based detail view for an author."""
    model = Author

class AuthorListView(generic.ListView):
    """Generic class-based list view for a list of authors."""
    model = Author
    template_name = 'catalog/author_list.html'
    #paginate_by = 5
    paginate_by = 10 #for the unittests

from django.contrib.auth.views import PasswordResetView

class PasswordResetView(PasswordResetView):

    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    success_url = '/password-reset/done/'

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact='o')
            .order_by('due_back')
        )

from django.contrib.auth.mixins import PermissionRequiredMixin

class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form =RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed'))
        
         # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Author

class AuthorCreate(PermissionRequiredMixin,CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}
    permission_required = 'catalog.can_mark_returned'

class AuthorUpdate( PermissionRequiredMixin, UpdateView):
    model = Author
    fields = '__all__' # Not recommended (potential security issue if more fields added)
    permission_required = 'catalog.can_mark_returned'

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.can_mark_returned'

from catalog.models import Book

class BookCreate(PermissionRequiredMixin,CreateView):
    model = Book
    fields = '__all__'
    #initial = {'date_of_death': '11/06/2020'}
    permission_required = 'catalog.can_mark_returned'

class BookUpdate( PermissionRequiredMixin, UpdateView):
    model = Book
    fields = '__all__' # Not recommended (potential security issue if more fields added)
    permission_required = 'catalog.can_mark_returned'

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'

from catalog.models import Genre

class GenreDetailView(generic.DetailView):
    """Generic class-based detail view for a genre."""
    model = Genre
    def genre_detail_view(request, primary_key):
        try:
            genre = Genre.objects.get(pk=primary_key)
        except Genre.DoesNotExist:
            raise Http404('Genre does not exist')

        return render(request, 'catalog/genre_detail.html', context={'genre': genre})

class GenreListView(generic.ListView):
    """Generic class-based view for a list of genres"""
    model = Genre
    context_object_name = 'genre_list'   # your own name for the list as a template variable
    #queryset = Book.objects.filter(title__icontains='The')[:5] # Get 5 books containing the title The
    template_name = 'catalog/genre_list.html'  # Specify your own template name/location
    paginate_by = 5

    def get_queryset(set):
        #return Genre.objects.filter(name__icontains='')[:10]
        #return Genre.objects.filter(name__iregex=r'^[A-Z]')
        return Genre.objects.all()
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(GenreListView, self).get_context_data(**kwargs)
        #context['some_data'] = 'This is just some data'
        genre = Genre.objects.all()
        context['genre'] = genre
        return context

class GenreCreate(PermissionRequiredMixin,CreateView):
    model = Genre
    fields = '__all__'
    #initial = {'date_of_death': '11/06/2020'}
    permission_required = 'catalog.can_mark_returned'

class GenreUpdate( PermissionRequiredMixin, UpdateView):
    model = Genre
    fields = '__all__' # Not recommended (potential security issue if more fields added)
    permission_required = 'catalog.can_mark_returned'

class GenreDelete(PermissionRequiredMixin, DeleteView):
    model = Genre
    success_url = reverse_lazy('genres')
    permission_required = 'catalog.can_mark_returned'