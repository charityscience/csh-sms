from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
# class IndexView(generic.ListView):
# 	template_name = 'polls/index.html'
# 	context_object_name = 'latest_question_list'

# 	def get_queryset(self):
# 		"""
# 		Return placeholder response
# 		"""
# 		return HttpResponse("Hello, world. You're at the polls index.")



def index(request):
	return HttpResponse("Hello, world. Management index")