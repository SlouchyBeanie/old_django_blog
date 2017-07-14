from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from django.db.models import Count
from .models import Post, Comment
from .forms import EmailPostForm, CommentForm
from taggit.models import Tag

def post_list(request, tag_slug=None):
	object_list = Post.published.all()
	tag = None

	if tag_slug:
		tag = get_object_or_404(Tag, slug=tag_slug)
		object_list = object_list.filter(tags__in=[tag])

	paginator = Paginator(object_list, 3) # 3 posts in each page
	page = request.GET.get('page')
	try:
		posts = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer deliver the first page
		posts = paginator.page(1)
	except EmptyPage:
		# If page is out of range deliver last page of results
		posts = paginator.page(paginator.num_pages)
	
	context = {
		'page' : page,
		'posts': posts,
		'tag': tag,
	}

	return render(request, 'blog/post/list.html', context)

'''class PostListView(ListView, tag_slug=None):
	queryset = Post.published.all()
	context_object_name = 'posts'
	paginate_by = 3
	template_name = 'blog/post/list.html'
	tag = None

	if tag_slug:
		tag = get_object_or_404(Tag, slug=tag_slug)
		object_list = object_list.filter(tags__in=[tag])'''

def post_detail(request, year, month, day, post):
	post = get_object_or_404(Post, slug=post,
								   status = 'published',
								   publish__year=year,
								   publish__month=month,
								   publish__day=day)
	
	# List of active comments for this post
	comments = post.comments.filter(active=True)

	if request.method == 'POST':
		# A comment was posted
		comment_form = CommentForm(data=request.POST)
		if comment_form.is_valid():
			# Create Comment object but don't save to database yet
			new_comment = comment_form.save(commit=False)
			# Assign the current post to the comment
			new_comment.post = post 			#new_comment.post != above post. This is the post in the Comment Model
			# Save the comment to the database
			new_comment.save()
	else:
		comment_form = CommentForm()

	# List of similiar posts
	post_tags_ids = post.tags.values_list('id', flat=True)
	similiar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
	similiar_posts = similiar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

	context = {
		'post': post,
		'comments': comments,
		'comment_form': comment_form,
		'similiar_posts': similiar_posts,
	}
	
	return render(request, 'blog/post/detail.html', context)


def post_share(request, post_id):
	#Retrieve post by id
	post = get_object_or_404(Post, id=post_id, status='published')
	sent = False
	receiver = ''

	if request.method == "POST":
		# Form was submitted
		form = EmailPostForm(request.POST)
		if form.is_valid():
			# Form fields passed validation
			cd = form.cleaned_data
			# ... send email
			post_url = request.build_absolute_uri(post.get_absolute_url())
			subject = '{} ({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
			message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
			send_mail(subject, message, 'brady.anderson28@gmail.com', [cd['to']])
			sent = True
			receiver = cd['to']
	else:
		form = EmailPostForm()

	context = {
		'post': post,
		'form': form,
		'sent': sent,
		'receiver': receiver,
	}
	
	return render(request, 'blog/post/share.html', context)