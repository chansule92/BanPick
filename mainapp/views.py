from django.http import HttpResponse
from django.template import loader
from django.db.models import Count, Sum, Subquery, OuterRef, Avg, Max,F, Q
import pandas as pd
from .models import champion_index





def index(request):
    student_information=champion_index.objects.values('EN','KR')
    template = loader.get_template("mainapp/index.html")
    pick = [0,1,2,3,4,5,6,7,8,9]
    champion0 = request.POST.get('champion0')
    champion1 = request.POST.get('champion1')
    champion2 = request.POST.get('champion2')
    champion3 = request.POST.get('champion3')
    champion4 = request.POST.get('champion4')
    champion5 = request.POST.get('champion5')
    champion6 = request.POST.get('champion6')
    champion7 = request.POST.get('champion7')
    champion8 = request.POST.get('champion8')
    champion9 = request.POST.get('champion9')
    value = [champion0,champion1,champion2,champion3,champion4,champion5,champion6,champion7,champion8,champion9]
    print(value)
    context = {
        "student_information":student_information,
        "pick":pick,
        "value" : value
    }
    return HttpResponse(template.render(context,request))

