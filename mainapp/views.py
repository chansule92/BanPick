from django.db import connection
import pandas as pd
from .models import champion_index
from django.shortcuts import render
import plotly.graph_objects as go
import numpy as np
import random
import plotly.express as px
from collections import defaultdict
import json
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, roc_auc_score
from .apps import MainappConfig 
import utils


def index(request):
    df = MainappConfig.global_df.get('df')
    df2 = MainappConfig.global_df.get('df2')
    dmg_rate_df = MainappConfig.global_df.get('dmg_rate_df')
    power_df = MainappConfig.global_df.get('power_df')
    gold_ml_df = MainappConfig.global_df.get('gold_ml_df')

    student_information = champion_index.objects.values('EN', 'KR')
    pick = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    blue_team = []
    red_team = []

    if request.method == 'POST':
        for i in range(5):
            blue_team.append(request.POST.get(f'champion{i}'))
        for i in range(5, 10):
            red_team.append(request.POST.get(f'champion{i}'))

    context = {
        "student_information": student_information,
        "pick": pick,
        "blue_team": blue_team,
        "red_team": red_team
    }
    return render(request, 'mainapp/index.html', context)

def result(request):
    if request.method == 'POST':
        selected_champions = request.POST.getlist('champion')
    stats = []
    for i in selected_champions:
        stats.append([df[df['Champion']==i.replace('%20',' ')]['Ban'].head(1).values,df[df['Champion']==i.replace('%20',' ')]['Pick'].head(1).values,df[df['Champion']==i.replace('%20',' ')]['Win_rate'].head(1).values])
    temp_chart_code=[]
    count=0
    blue_team = []
    red_team = []
    for i in selected_champions:
        if count < 5:
            blue_team.append(i.replace('%20',' '))
        else:
            red_team.append(i.replace('%20',' '))
        count=count+1
    pred = final_model.predict(ml_features(blue_team,red_team))
    pred_proba = final_model.predict_proba(ml_features(blue_team,red_team))[:, 1]
    result_df = [round(pred_proba[0]*100,1),round((1-pred_proba[0])*100,1)]
    temp_chart_code = []
    temp_chart_code.append(duo_chart(blue_team)[0])
    temp_chart_code.append(count_chart(blue_team,red_team)[0])
    temp_chart_code.append(duo_chart(red_team)[0])
    temp_chart_code.append(count_chart(red_team,blue_team)[0])
    temp_chart_code.append(create_power_graph(power_graph(blue_team)))
    temp_chart_code.append(create_power_graph(power_graph(red_team)))
    temp_chart_code.append(dmg_weight_chart(dmg_weight(blue_team)))
    temp_chart_code.append(dmg_weight_chart(dmg_weight(red_team)))
    temp_chart_code.append(damage_distribution(blue_team)[0])
    temp_chart_code.append(damage_distribution(red_team)[0])
    test=power_df
    print(blue_team)
    print(red_team)
    context = {
        'champions': selected_champions,
        'stats': stats,
        'temp_chart_code': temp_chart_code,
        "value": result_df,
        "test":test
    }
    return render(request, 'mainapp/result.html', context)


def report(request):
    if request.method == 'POST':
        selected_champions = request.POST.getlist('champion')
    stats = []
    for i in selected_champions:
        stats.append([df[df['Champion']==i.replace('%20',' ')]['Ban'].head(1).values,df[df['Champion']==i.replace('%20',' ')]['Pick'].head(1).values,df[df['Champion']==i.replace('%20',' ')]['Win_rate'].head(1).values])
    temp_chart_code=[]
    count=0
    blue_team = []
    red_team = []
    for i in selected_champions:
        if count < 5:
            blue_team.append(i.replace('%20',' '))
        else:
            red_team.append(i.replace('%20',' '))
        count=count+1
#    blue_team = ['rumble', 'naafiri', 'ahri', 'kaisa', 'leona']
#    red_team = ['gwen', 'pantheon', 'azir', 'jhin', 'rell']
    print(blue_team)
    print(red_team)
    blue_gold_comment_code=[]
    red_gold_comment_code=[]
    gold_comment=pd.concat([gold(blue_team),gold(red_team)],axis=1)
    gold_comment.columns=['Time','blue_gold','-','red_gold']
    gold_comment['diff_gold']=gold_comment['blue_gold']-gold_comment['red_gold']
    if float(gold_comment[gold_comment['Time']=='early']['diff_gold'].iloc[0]) >= 10 :
        blue_gold_comment_code.append('우세')
        red_gold_comment_code.append('열세')
    elif float(gold_comment[gold_comment['Time']=='early']['diff_gold'].iloc[0]) <= -10:
        blue_gold_comment_code.append('열세')
        red_gold_comment_code.append('우세')
    else:
        blue_gold_comment_code.append('대등')
        red_gold_comment_code.append('대등')
    if float(gold_comment[gold_comment['Time']=='middle']['diff_gold'].iloc[0]) >= 10 :
        blue_gold_comment_code.append('우세')
        red_gold_comment_code.append('열세')
    elif float(gold_comment[gold_comment['Time']=='middle']['diff_gold'].iloc[0]) <= -10:
        blue_gold_comment_code.append('열세')
        red_gold_comment_code.append('우세')
    else:
        blue_gold_comment_code.append('대등')
        red_gold_comment_code.append('대등')
    if float(gold_comment[gold_comment['Time']=='late']['diff_gold'].iloc[0]) >= 20 :
        blue_gold_comment_code.append('우세')
        red_gold_comment_code.append('열세')
    elif float(gold_comment[gold_comment['Time']=='late']['diff_gold'].iloc[0]) <= -20:
        blue_gold_comment_code.append('열세')
        red_gold_comment_code.append('우세')
    else:
        blue_gold_comment_code.append('대등')
        red_gold_comment_code.append('대등')
    pred = final_model.predict(ml_features(blue_team,red_team))
    pred_proba = final_model.predict_proba(ml_features(blue_team,red_team))[:, 1]
    result_df = [round(pred_proba[0]*100,1),round((1-pred_proba[0])*100,1)]
    temp_chart_code = []
    temp_chart_code.append(duo_chart(blue_team)[0])
    temp_chart_code.append(count_chart(blue_team,red_team)[0])
    temp_chart_code.append(duo_chart(red_team)[0])
    temp_chart_code.append(count_chart(red_team,blue_team)[0])
    temp_chart_code.append(create_power_graph(power_graph(blue_team)))
    temp_chart_code.append(create_power_graph(power_graph(red_team)))
    temp_chart_code.append(dmg_weight_chart(dmg_weight(blue_team)))
    temp_chart_code.append(dmg_weight_chart(dmg_weight(red_team)))
    temp_chart_code.append(damage_distribution(blue_team)[0])
    temp_chart_code.append(damage_distribution(red_team)[0])
    test=power_df
    comment_code=[]
    comment_code.append(duo_chart(blue_team)[1])
    comment_code.append(count_chart(blue_team,red_team)[1])
    comment_code.append(duo_chart(red_team)[1])
    comment_code.append(count_chart(red_team,blue_team)[1])
    comment_code.append(blue_gold_comment_code)
    comment_code.append(red_gold_comment_code)
    comment_code.append(dmg_weight_chart_comment(blue_team,red_team))
    comment_code.append(dmg_weight_chart_comment(red_team,blue_team))
    comment_code.append(damage_distribution(blue_team)[1])
    comment_code.append(damage_distribution(red_team)[1])

    replacements = get_replacements()
    replacements_json = json.dumps(replacements)

    context = {
        'champions': selected_champions,
        'stats': stats,
        'temp_chart_code': temp_chart_code,
        'comment_code': comment_code,
        "value": result_df,
        "test":test,
        'replacements': replacements_json
    }
    return render(request, 'mainapp/report.html', context)
