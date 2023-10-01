from django.shortcuts import render
from django.views import generic

# Create your views here.
from .models import Book, Author, BookInstance, Genre

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    # Available books (that contain python)
    num_instances_python = Book.objects.filter(title__contains = 'Favor').count()

    #Available genres
    num_genres = Genre.objects.all().count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_instances_python' : num_instances_python,
        'num_genres' : num_genres,
        'num_visits' : num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BookListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        context['some_data'] = 'This is just some data'
        return context
    #context_object_name = 'book_list'   # your own name for the list as a template variable
    
    def get_queryset(self):
        return Book.objects.filter(title__icontains='')[:] # Get 5 books containing the title war
    # queryset = Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war
    
    template_name = 'books/my_arbitrary_template_name_list.html'  # Specify your own template name/location

    paginate_by = 2

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(AuthorListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        context['some_data'] = 'This is just some data'
        return context
    #context_object_name = 'book_list'   # your own name for the list as a template variable
    
    def get_queryset(self):
        return Author.objects.filter(first_name__icontains='')[:]
         # Get 5 books containing the title war
    # queryset = Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war
    
    template_name = 'books/my_arbitrary_template_name_list.html'  # Specify your own template name/location

    paginate_by = 2

class AuthorDetailView(generic.DetailView):
    model = Author


from django.contrib.auth.mixins import LoginRequiredMixin

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

class AllBorrowedBooksView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'catalog.can_mark_returned'
    # Or multiple permissions
    # *******permission_required = ('catalog.can_mark_returned', 'catalog.can_edit')
    # Note that 'catalog.can_edit' is just an example
    # the catalog application doesn't have such permission!

    model = BookInstance
    template_name = 'catalog/bookinstance_list_all_borrowed.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter()
            .filter(status__exact='o')
            .order_by('due_back')
        )

class AllBookInstancesView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'catalog.can_mark_returned'
    # Or multiple permissions
    # *******permission_required = ('catalog.can_mark_returned', 'catalog.can_edit')
    # Note that 'catalog.can_edit' is just an example
    # the catalog application doesn't have such permission!

    model = BookInstance
    template_name = 'catalog/all-book-instances.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter()
            #.filter(status__exact='o')
            .order_by('due_back')
        )

 ### THE VIEW FOR RENEWING RETURN DATE BY A LOGGED-IN LIBRARIAN WHO HAS THE PERMISSION TO RENEW THE RETURN DATE ###
import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from catalog.forms import RenewBookForm

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

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


## VIEW TO ALLOW FOR EDITING AUTHOR DETAILS (meant to be similar to that in the admin site)
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Author


class AuthorCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_mark_returned'

    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    fields = '__all__' # Not recommended (potential security issue if more fields added)

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    success_url = reverse_lazy('authors')


## VIEW TO ALLOW FOR EDITING BOOK DETAILS (meant to be similar to that in the admin site)

from catalog.models import Book


class BookCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_mark_returned'

    model = Book
    fields = '__all__' #['title', 'author', 'summary', 'isbn', 'genre', 'language']
   # initial = {'date_of_death': '11/06/2020'}

class BookUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    fields = '__all__' # Not recommended (potential security issue if more fields added)

class BookDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    success_url = reverse_lazy('books')


## VIEW TO ALLOW FOR EDITING BOOK INSTANCE DETAILS (meant to be similar to that in the admin site)

from catalog.models import BookInstance


class BookInstanceCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_mark_returned'

    model = BookInstance
    fields = '__all__' #['title', 'author', 'summary', 'isbn', 'genre', 'language']
   # initial = {'date_of_death': '11/06/2020'}

class BookInstanceUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = BookInstance
    fields = '__all__' # Not recommended (potential security issue if more fields added)


class BookInstanceDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = BookInstance
    success_url = reverse_lazy('all-book-instances')

    template_name = 'catalog/bookinstance_confirm_delete.html'  # Template for delete confirmation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book_instance'] = self.object  # Pass the BookInstance object to the template
        return context

class BookInstanceDetailView(generic.DetailView):
    model = BookInstance