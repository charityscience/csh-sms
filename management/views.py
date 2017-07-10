from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import Contact, Group

# Create your views here.
class IndexView(generic.ListView):
	template_name = 'management/index.html'
	context_object_name = 'latest_contact_list'

	def get_queryset(self):
		"""
		Return the 5 most recent sign ups
		"""
		return Contact.objects.order_by('-date_of_sign_up')[:5]



class DetailView(generic.DetailView):
    model = Contact
    template_name = 'management/detail.html'