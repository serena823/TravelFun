from django.shortcuts import render, reverse, get_object_or_404
from .models import Post, Comment, Notification
from django.apps import apps
from django.contrib.auth.models import User
from django.views.generic import (
    ListView, DetailView,
    CreateView, UpdateView, DeleteView
    )
# ListView class that you can use to display
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.db.models import Q

from django.http import HttpResponse
from geopy.geocoders import Nominatim

import re
from itertools import chain


class Home(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'photo_blog/home.html'
    paginate_by = 4

# Queryset returned is posts with authors the authenticated user follows.
# get_queryset: Get the list of items for this view. 
    def get_queryset(self):
        following = []
        pk = self.request.user
        for user in User.objects.all():
            if pk in user.profile.followers.all():
                following.append(user.pk)
        object_list = Post.objects.filter(author_id__in=following).order_by('-date_posted')
        return object_list



def search(request):
    queryset = None
    query = request.GET.get('q')

    if 'searchuser' in request.GET:
        #print("search user1")
        if query:
            Profile = apps.get_model('users', 'Profile')
            queryset = Profile.objects.all().filter(
                Q(user__username__icontains=query)
                ).distinct()
            #print("search user2")
        context = {
            'posts1': queryset    # search user
        }
        #print("search user3")
        return render(request, "photo_blog/search.html", context)

    if 'searchlocation' in request.GET:
        #print("search post1")
        if query:
            queryset = Post.objects.all().filter(
                Q(geolocation__icontains=query)
            ).distinct()
            #print("search post2")
        context = {
            'posts2': queryset    # search post
        }
        #print("search post3")
        return render(request, "photo_blog/search.html", context)

    context = {
        'posts': queryset
    }
    return render(request, "photo_blog/search.html", context)





class ViewProfile(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'photo_blog/user_profile.html'
    context_object_name ='posts'
    ordering = ['-date_posted']

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return User.objects.filter(username=user)


class ViewPost(LoginRequiredMixin, DetailView):
    model = Post


class CreatePost(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['photo', 'caption', 'location', 'geolocation', 'lat', 'lon']

    def form_valid(self, form):
        if (self.request.POST['location']):
            location1 = str(self.request.POST['location'])
            # print(location1)
            r = re.compile(r'\([-]*\d.*\d+[ ]*[-]*\d.*\d+\)')
            coor = r.findall(location1)
            a = coor[0].split()
            lat = re.sub(r'\(', "", a[0])
            lon = re.sub(r'\)', "", a[1])
            #print(lat)
            #print(lon)
            geolocator = Nominatim()
            location2 = geolocator.reverse((lat, lon))
            #print(location2.address)
            form.instance.lat = lat
            form.instance.lon = lon
            form.instance.geolocation = location2.address
        form.instance.author = self.request.user
        return super().form_valid(form)



class UpdatePost(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['caption']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class DeletePost(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    sucess_url = 'photo_blog-home'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


    def get_success_url(self):
        return reverse('photo_blog-home')


class CreateComment(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['text']

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        pk = self.kwargs.get('pk')
        return reverse('photo_blog-detail', args={pk: 'pk'})


class DeleteComment(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    sucess_url = '/'

    def test_func(self):
        comment = self.get_object()
        if self.request.user == comment.author:
            return True
        return False

    def get_success_url(self, **kwargs):
        pk = self.object.post.pk
        return reverse( 'photo_blog-detail', args={pk: 'pk'})



# This view creates a REST API. Everytime the REST API is accessed through a
# jQuery button, the authenticated user is added/removed from the list of users
# who have liked the post.
class LikePostAPI(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, slug=None, format=None, pk=None):
        obj = get_object_or_404(Post, id=pk)
        user = self.request.user
        updated = False
        liked = False
        if user.is_authenticated:
            if user in obj.likes.all():
                liked = False
                obj.likes.remove(user)
                like_count = obj.likes.count()
                img = '<img src="/media/nav_buttons/unliked.svg" height="17" width="17">'
            else:
                liked = True
                obj.likes.add(user)
                like_count = obj.likes.count()
                img = '<img src="/media/nav_buttons/liked.svg" height="17" width="17">'
            updated = True
        data = {
            "updated": updated,
            "liked": liked,
            "like_count": like_count,
            "img": img
        }
        return Response(data)


class ViewLikes(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'photo_blog/post_likes.html'
    context_object_name ='post'
    ordering = ['-date_posted']

    def get_queryset(self):
        post = get_object_or_404(Post, id=self.kwargs.get('pk'))
        return post


# Queryset returns three types of notifications specific to each user.
class ViewNotifications(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'photo_blog/notifications.html'

    def get_queryset(self):
        object_list = Notification.objects.filter(
        Q(profile_id=self.request.user.id) |
        ~Q(user=self.request.user)
        )
        return object_list
