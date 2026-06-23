from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import PublicationForm
from .models import Publication, PublicationPhoto


@login_required
def publication_feed(request):
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save(commit=False)
            publication.author = request.user
            publication.save()
            for photo in form.cleaned_data.get('photos', []):
                PublicationPhoto.objects.create(publication=publication, image=photo)
            messages.success(request, 'Publicacion creada.')
            return redirect('publication_feed')
    else:
        form = PublicationForm()

    publications = (
        Publication.objects
        .select_related('author__profile')
        .prefetch_related('photos')
    )
    return render(request, 'publications/feed.html', {
        'form': form,
        'publications': publications,
    })
