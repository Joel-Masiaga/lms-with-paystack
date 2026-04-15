import sys
from lms.settings import *
import django
django.setup()
from django.urls import reverse
print(reverse('register'))
