from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .forms import PublicationForm
from .models import Publication, PublicationComment, PublicationLike, PublicationPhoto


class LinkPreviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.title = ''
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self._in_title = True
        if tag != 'meta':
            return
        key = attrs.get('property') or attrs.get('name')
        content = attrs.get('content')
        if key and content and key not in self.meta:
            self.meta[key] = content.strip()

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()


def fetch_link_preview(url):
    if not url:
        return {}
    try:
        request = Request(url, headers={'User-Agent': 'Afinia link preview'})
        with urlopen(request, timeout=4) as response:
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                return {}
            html = response.read(250000).decode(response.headers.get_content_charset() or 'utf-8', errors='ignore')
    except Exception:
        return {}

    parser = LinkPreviewParser()
    parser.feed(html)
    image_url = parser.meta.get('og:image') or parser.meta.get('twitter:image') or ''
    title = parser.meta.get('og:title') or parser.meta.get('twitter:title') or parser.title
    description = parser.meta.get('og:description') or parser.meta.get('description') or parser.meta.get('twitter:description') or ''
    return {
        'link_title': (title or '')[:220],
        'link_description': (description or '')[:500],
        'link_image_url': urljoin(url, image_url) if image_url else '',
    }


@login_required
def publication_feed(request):
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save(commit=False)
            publication.author = request.user
            for field, value in fetch_link_preview(publication.link_url).items():
                setattr(publication, field, value)
            publication.save()
            for photo in form.cleaned_data.get('photos', []):
                PublicationPhoto.objects.create(publication=publication, image=photo)
            messages.success(request, 'Publicación creada.')
            return redirect('publication_feed')
    else:
        form = PublicationForm()

    publications = (
        Publication.objects
        .select_related('author__profile')
        .prefetch_related('photos', 'comments__author__profile', 'likes')
    )
    liked_publication_ids = set(
        PublicationLike.objects
        .filter(user=request.user, publication__in=publications)
        .values_list('publication_id', flat=True)
    )
    return render(request, 'publications/feed.html', {
        'form': form,
        'publications': publications,
        'liked_publication_ids': liked_publication_ids,
    })


@login_required
@require_POST
def publication_like(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    like, created = PublicationLike.objects.get_or_create(publication=publication, user=request.user)
    if not created:
        like.delete()
    return redirect('publication_feed')


@login_required
@require_POST
def publication_comment(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    body = (request.POST.get('body') or '').strip()
    if not body:
        messages.info(request, 'Escribe un comentario antes de publicarlo.')
        return redirect('publication_feed')
    PublicationComment.objects.create(
        publication=publication,
        author=request.user,
        body=body[:500],
    )
    return redirect('publication_feed')
