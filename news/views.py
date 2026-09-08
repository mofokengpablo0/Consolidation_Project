"""View handlers for the News application, managing articles, publishers, and newsletters."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden

from .models import Article, Publisher, Newsletter
from .forms import ArticleForm
from .permissions import IsEditor, IsJournalist, IsReader, IsArticleAuthorOrEditor

User = get_user_model()


def home(request):
    """Render the home page featuring the latest approved articles and active publishers."""
    articles = Article.objects.filter(approved=True)[:12]
    publishers = Publisher.objects.filter(is_active=True)[:6]

    context = {
        "articles": articles,
        "publishers": publishers,
    }
    return render(request, "news/home.html", context)


def article_list(request):
    """Render a searchable list of approved articles, optionally filtered by publisher."""
    query = request.GET.get("q", "")
    publisher_id = request.GET.get("publisher", "")

    articles = Article.objects.filter(approved=True)

    if query:
        articles = articles.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(summary__icontains=query)
        )

    if publisher_id:
        articles = articles.filter(publisher_id=publisher_id)

    publishers = Publisher.objects.filter(is_active=True)

    context = {
        "articles": articles,
        "publishers": publishers,
        "query": query,
        "selected_publisher": publisher_id,
    }
    return render(request, "news/article_list.html", context)


def article_detail(request, article_id):
    """Render the detailed view of an article; restricts unapproved content to authors/editors."""
    article = get_object_or_404(Article, id=article_id)

    if not article.approved:
        if not request.user.is_authenticated or (
            request.user != article.author and request.user.role != "editor"
        ):
            messages.error(request, "This article is not yet published.")
            return redirect("news:article_list")

    context = {"article": article}
    return render(request, "news/article_detail.html", context)


@login_required
def article_create(request):
    """Handle the creation of new articles; restricted to users with the journalist role."""
    if request.user.role != "journalist":
        return HttpResponseForbidden("Only journalists can create articles.")

    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            messages.success(request, "Article submitted for review!")
            return redirect("news:article_detail", article_id=article.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ArticleForm()

    context = {"form": form}
    return render(request, "news/article_form.html", context)


@login_required
def article_edit(request, article_id):
    """Handle the editing of articles; restricted to the original author or an editor."""
    article = get_object_or_404(Article, id=article_id)

    if article.author != request.user and request.user.role != "editor":
        return HttpResponseForbidden("You can only edit your own articles.")

    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article updated successfully!")
            return redirect("news:article_detail", article_id=article.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ArticleForm(instance=article)

    context = {
        "article": article,
        "form": form,
    }
    return render(request, "news/article_form.html", context)


@login_required
def article_delete(request, article_id):
    """Handle article deletion; restricted to the original author or an editor."""
    article = get_object_or_404(Article, id=article_id)

    if article.author != request.user and request.user.role != "editor":
        return HttpResponseForbidden("You can only delete your own articles.")

    if request.method == "POST":
        article.delete()
        messages.success(request, "Article deleted.")
        return redirect("news:article_list")

    context = {"article": article}
    return render(request, "news/article_confirm_delete.html", context)


@login_required
def article_approve(request, article_id):
    """Handle the approval of an article; restricted to editors."""
    article = get_object_or_404(Article, id=article_id)

    if request.user.role != "editor":
        return HttpResponseForbidden("Only editors can approve articles.")

    if request.method == "POST":
        article.approved = True
        article.approved_by = request.user
        article.save()  # Triggers signal
        messages.success(request, f"Article approved! Subscribers have been notified.")
        return redirect("news:article_detail", article_id=article.id)

    context = {"article": article}
    return render(request, "news/article_approve_confirm.html", context)


@login_required
def editor_dashboard(request):
    """Render a dashboard for editors to manage pending and published articles."""
    if request.user.role != "editor":
        return HttpResponseForbidden("Editors only.")

    pending_articles = Article.objects.filter(approved=False)
    approved_articles = Article.objects.filter(approved=True)[:10]

    context = {
        "pending_articles": pending_articles,
        "approved_articles": approved_articles,
    }
    return render(request, "news/editor_dashboard.html", context)


def publisher_list(request):
    """Render a list of all active publishers."""
    publishers = Publisher.objects.filter(is_active=True)
    return render(request, "news/publisher_list.html", {"publishers": publishers})


def publisher_detail(request, publisher_id):
    """Render the details and approved articles for a specific publisher."""
    publisher = get_object_or_404(Publisher, id=publisher_id, is_active=True)
    articles = publisher.articles.filter(approved=True)

    context = {
        "publisher": publisher,
        "articles": articles,
    }
    return render(request, "news/publisher_detail.html", context)


@login_required
def subscribe_publisher(request, publisher_id):
    """Handle subscription and unsubscription logic for a publisher."""
    publisher = get_object_or_404(Publisher, id=publisher_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "subscribe":
            request.user.subscribed_publishers.add(publisher)
            messages.success(request, f"Subscribed to {publisher.name}!")
        elif action == "unsubscribe":
            request.user.subscribed_publishers.remove(publisher)
            messages.success(request, f"Unsubscribed from {publisher.name}")

    return redirect("news:publisher_detail", publisher_id=publisher_id)


@login_required
def subscribe_journalist(request, journalist_id):
    """Handle subscription and unsubscription logic for a journalist."""
    journalist = get_object_or_404(User, id=journalist_id, role="journalist")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "subscribe":
            request.user.subscribed_journalists.add(journalist)
            messages.success(request, f"Subscribed to {journalist.username}!")
        elif action == "unsubscribe":
            request.user.subscribed_journalists.remove(journalist)
            messages.success(request, f"Unsubscribed from {journalist.username}")

    return redirect("news:journalist_detail", journalist_id=journalist_id)


def journalist_detail(request, journalist_id):
    """Render the profile and approved articles of a specific journalist."""
    journalist = get_object_or_404(User, id=journalist_id, role="journalist")
    articles = journalist.authored_articles.filter(approved=True)

    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = request.user.subscribed_journalists.filter(
            id=journalist.id
        ).exists()

    context = {
        "journalist": journalist,
        "articles": articles,
        "is_subscribed": is_subscribed,
    }
    return render(request, "news/journalist_detail.html", context)


def journalist_list(request):
    """Render a list of all active journalists."""
    journalists = User.objects.filter(role="journalist", is_active=True)
    return render(request, "news/journalist_list.html", {"journalists": journalists})


@login_required
def newsletter_list(request):
    """Render a list of the most recent newsletters."""
    newsletters = Newsletter.objects.all().order_by("-created_at")[:20]
    return render(request, "news/newsletter_list.html", {"newsletters": newsletters})


@login_required
def newsletter_create(request):
    """Handle the creation of newsletters; restricted to journalists and editors."""
    if request.user.role not in ["journalist", "editor"]:
        return HttpResponseForbidden(
            "Only journalists and editors can create newsletters."
        )

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        article_ids = request.POST.getlist("articles")

        newsletter = Newsletter.objects.create(
            title=title,
            description=description,
            author=request.user,
        )

        if article_ids:
            newsletter.articles.set(article_ids)

        messages.success(request, "Newsletter created!")
        return redirect("news:newsletter_detail", newsletter_id=newsletter.id)

    articles = Article.objects.filter(approved=True)
    context = {"articles": articles}
    return render(request, "news/newsletter_form.html", context)


def newsletter_detail(request, newsletter_id):
    """Render the detailed content of a specific newsletter."""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    context = {"newsletter": newsletter}
    return render(request, "news/newsletter_detail.html", context)
