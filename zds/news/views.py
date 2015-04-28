# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from zds import settings
from zds.member.models import Profile
from zds.news.forms import NewsForm, MessageNewsForm
from zds.news.models import News, MessageNews
from zds.utils.paginator import ZdSPagingListView


class NewsList(ZdSPagingListView):
    """
    Displays the list of news.
    """

    context_object_name = 'news_list'
    paginate_by = settings.ZDS_APP['news']['news_per_page']
    queryset = News.objects.all()
    template_name = 'news/index.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('news.change_news', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(NewsList, self).dispatch(request, *args, **kwargs)


class NewsCreate(CreateView):
    """
    Creates a new news.
    """

    form_class = NewsForm
    template_name = 'news/create.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('news.change_news', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(NewsCreate, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        news = News()
        news.title = form.data.get('title')
        news.type = form.data.get('type')
        news.image_url = form.data.get('image_url')
        news.url = form.data.get('url')
        news.pubdate = datetime.now()
        news.save()
        for author in form.data.get('authors').split(","):
            current = author.strip()
            if current == '':
                continue
            current_author = get_object_or_404(Profile, user__username=current)
            news.authors.add(current_author)
        news.save()

        return redirect(reverse('news-list'))


class NewsUpdate(UpdateView):
    """
    Updates a news
    """

    form_class = NewsForm
    template_name = 'news/update.html'
    queryset = News.objects.all()
    news = None

    @method_decorator(login_required)
    @method_decorator(permission_required('news.change_news', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(NewsUpdate, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.news = self.get_object()
        form = self.form_class(initial={
            'title': self.news.title,
            'type': self.news.type,
            'image_url': self.news.image_url,
            'url': self.news.url,
            'authors': ", ".join([author.user.username for author in self.news.authors.all()])
        })
        form.helper.form_action = reverse('news-update', args=[self.news.pk])
        return render(request, self.template_name, {'form': form, 'news': self.news})

    def post(self, request, *args, **kwargs):
        self.news = self.get_object()
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form, 'news': self.news})

    def form_valid(self, form):
        self.news.title = form.data.get('title')
        self.news.type = form.data.get('type')
        self.news.image_url = form.data.get('image_url')
        self.news.url = form.data.get('url')
        self.news.pubdate = datetime.now()
        self.news.save()
        for author in form.data.get('authors').split(","):
            current = author.strip()
            if current == '':
                continue
            current_author = get_object_or_404(Profile, user__username=current)
            self.news.authors.add(current_author)
        self.news.save()

        return redirect(reverse('zds.pages.views.home'))

    def get_form(self, form_class):
        form = self.form_class(self.request.POST)
        form.helper.form_action = reverse('news-update', args=[self.news.pk])
        return form


class NewsDeleteDetail(SingleObjectMixin, RedirectView):
    """
    Deletes a news
    """
    queryset = News.objects.all()

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    @method_decorator(permission_required('news.change_news', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(NewsDeleteDetail, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        news = self.get_object()
        news.delete()

        messages.success(request, _(u'La une a été supprimée avec succès.'))

        return redirect(reverse('news-list'))


class NewsDeleteList(MultipleObjectMixin, RedirectView):
    """
    Deletes a list of news
    """

    @method_decorator(login_required)
    @method_decorator(permission_required('news.change_news', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(NewsDeleteList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        list = self.request.POST.getlist('items')
        return News.objects.filter(pk__in=list)

    def post(self, request, *args, **kwargs):
        for news in self.get_queryset():
            news.delete()

        messages.success(request, _(u'Les unes ont été supprimées avec succès.'))

        return redirect(reverse('news-list'))


class MessageNewsCreateUpdate(CreateView):
    """
    Creates or updates the new message.
    """

    form_class = MessageNewsForm
    template_name = 'news/message/create.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('news.change_news', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(MessageNewsCreateUpdate, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        last_message = MessageNews.objects.get_last_message()
        if last_message:
            last_message.delete()
        message_news = MessageNews()
        message_news.message = form.data.get('message')
        message_news.url = form.data.get('url')
        message_news.save()
        return redirect(reverse('zds.pages.views.home'))
