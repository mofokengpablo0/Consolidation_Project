from django.contrib import admin
from .models import Article, Publisher, Newsletter, Subscription, ApprovedArticleLog


class ArticleInline(admin.TabularInline):
    model = Article
    extra = 0
    fields = ['title', 'author', 'approved', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'get_subscriber_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['editors', 'journalists']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'publisher', 'approved', 
                    'created_at', 'get_status']
    list_filter = ['approved', 'created_at', 'publisher']
    search_fields = ['title', 'content']
    readonly_fields = ['approved_at', 'approved_by', 'created_at', 
                       'updated_at', 'published_date']
    
    actions = ['approve_articles']
    
    def approve_articles(self, request, queryset):
        for article in queryset.filter(approved=False):
            article.approved = True
            article.approved_by = request.user
            article.save()
    approve_articles.short_description = "Approve selected articles"


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'get_article_count', 'created_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['articles']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'publisher', 'journalist', 'subscribed_at']
    list_filter = ['subscribed_at']


@admin.register(ApprovedArticleLog)
class ApprovedArticleLogAdmin(admin.ModelAdmin):
    list_display = ['article', 'posted_to_api', 'emailed_to_subscribers',
                    'subscribers_count', 'created_at']
    list_filter = ['posted_to_api', 'emailed_to_subscribers', 'created_at']
