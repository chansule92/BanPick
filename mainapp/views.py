import pandas as pd
from .models import champion_index
from django.shortcuts import render
from .apps import MainappConfig
from . import utils
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK", status=200)


def index(request):
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
    df = MainappConfig.global_df.get('df')
    dmg_rate_df = MainappConfig.global_df.get('dmg_rate_df')
    power_df = MainappConfig.global_df.get('power_df')
    gold_ml_df = MainappConfig.global_df.get('gold_ml_df')
    final_model = MainappConfig.ml_model
    dmg_weight_dict = MainappConfig.dmg_weight_dict
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
    pred_proba = final_model.predict_proba(utils.ml_features(blue_team,red_team,gold_ml_df,df, dmg_rate_df))[:, 1]
    result_df = [round(pred_proba[0]*100,1),round((1-pred_proba[0])*100,1)]
    temp_chart_code = []
    temp_chart_code.append(utils.duo_chart(blue_team,df)[0])
    temp_chart_code.append(utils.count_chart(blue_team,red_team,df)[0])
    temp_chart_code.append(utils.duo_chart(red_team,df)[0])
    temp_chart_code.append(utils.count_chart(red_team,blue_team,df)[0])
    temp_chart_code.append(utils.create_power_graph(utils.power_graph(blue_team,power_df)))
    temp_chart_code.append(utils.create_power_graph(utils.power_graph(red_team,power_df)))
    temp_chart_code.append(utils.dmg_weight_chart(utils.dmg_weight(blue_team,dmg_weight_dict)))
    temp_chart_code.append(utils.dmg_weight_chart(utils.dmg_weight(red_team,dmg_weight_dict)))
    temp_chart_code.append(utils.damage_distribution(blue_team,dmg_rate_df)[0])
    temp_chart_code.append(utils.damage_distribution(red_team,dmg_rate_df)[0])
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
    df = MainappConfig.global_df.get('df')
    print(df.head(1))
    dmg_rate_df = MainappConfig.global_df.get('dmg_rate_df')
    print(dmg_rate_df.head(1))
    power_df = MainappConfig.global_df.get('power_df')
    print(power_df.head(1))
    gold_ml_df = MainappConfig.global_df.get('gold_ml_df')
    print(gold_ml_df.head(1))
    final_model = MainappConfig.ml_model
    print(final_model)
    dmg_weight_dict = MainappConfig.dmg_weight_dict

    if request.method == 'POST':
        selected_champions = request.POST.getlist('champion')
    stats = []
    for i in selected_champions:
        i_clean = i.replace('%20',' ')
        try:
            ban_val = df[df['Champion']==i_clean]['Ban'].head(1).values[0]
        except:
            ban_val = 0
        try:
            pick_val = df[df['Champion']==i_clean]['Pick'].head(1).values[0]
        except:
            pick_val = 0
        try:
            win_val = df[df['Champion']==i_clean]['Win_rate'].head(1).values[0]
        except:
            win_val = 0
        stats.append([ban_val, pick_val, win_val])
#    for i in selected_champions:
#        i_clean = i.replace('%20',' ')
#        data = champion_stats_dict.get(i_clean, {'Ban': 0, 'Pick': 0, 'Win_rate': 0})
#        stats.append([data['Ban'], data['Pick'], data['Win_rate']])
    print(stats)
    blue_team = [c.replace('%20',' ') for i, c in enumerate(selected_champions) if i < 5]
    red_team = [c.replace('%20',' ') for i, c in enumerate(selected_champions) if i >= 5]

    gold_comment = pd.concat([utils.gold(blue_team, power_df), utils.gold(red_team, power_df)], axis=1)
    gold_comment.columns = ['Time', 'blue_gold', '-', 'red_gold']
    gold_comment['diff_gold'] = gold_comment['blue_gold'] - gold_comment['red_gold']

    gold_comment.set_index('Time', inplace=True)

    blue_gold_comment_code = []
    red_gold_comment_code = []

    def get_comment(time_key, blue_threshold, red_threshold=None):
        red_threshold = red_threshold if red_threshold is not None else blue_threshold

        try:
            diff = gold_comment.loc[time_key, 'diff_gold']
        except KeyError:
            return '대등', '대등'

        if diff >= blue_threshold:
            return '우세', '열세'
        elif diff <= -red_threshold:
            return '열세', '우세'
        else:
            return '대등', '대등'

    b_early, r_early = get_comment('early', 10)
    blue_gold_comment_code.append(b_early)
    red_gold_comment_code.append(r_early)

    b_mid, r_mid = get_comment('mid', 10)
    blue_gold_comment_code.append(b_mid)
    red_gold_comment_code.append(r_mid)

    b_late, r_late = get_comment('late', 20)
    blue_gold_comment_code.append(b_late)
    red_gold_comment_code.append(r_late)


    print('ml_predict_start')

    ml_features_result = utils.ml_features(blue_team, red_team, gold_ml_df, df, dmg_weight_dict)
    try:
        if hasattr(final_model, 'set_params'):
            final_model.set_params(n_jobs=1)
            print("XGBoost n_jobs set to 1 for stability.")
    except Exception as e:
        print(f"Failed to set n_jobs=1 on final_model: {e}")

    pred_proba = final_model.predict_proba(ml_features_result.values)[:, 1]
    result_df = [round(pred_proba[0] * 100, 1), round((1 - pred_proba[0]) * 100, 1)]
    # pred = final_model.predict(ml_features_result)
    print('ml_predict_end')

    print('chart_start')
    blue_duo_chart, blue_duo_comment = utils.duo_chart(blue_team, df)
    blue_count_chart, blue_count_comment = utils.count_chart(blue_team, red_team, df)
    blue_dmg_dist_chart, blue_dmg_dist_comment = utils.damage_distribution(blue_team, dmg_rate_df)
    blue_power_graph = utils.power_graph(blue_team, power_df)
    blue_dmg_weight_data = utils.dmg_weight(blue_team, dmg_weight_dict)
    blue_dmg_weight_comment = utils.dmg_weight_chart_comment(blue_team, red_team, gold_ml_df, df, dmg_weight_dict)

    red_duo_chart, red_duo_comment = utils.duo_chart(red_team, df)
    red_count_chart, red_count_comment = utils.count_chart(red_team, blue_team, df)
    red_dmg_dist_chart, red_dmg_dist_comment = utils.damage_distribution(red_team, dmg_rate_df)
    red_power_graph = utils.power_graph(red_team, power_df)
    red_dmg_weight_data = utils.dmg_weight(red_team, dmg_weight_dict)
    red_dmg_weight_comment = utils.dmg_weight_chart_comment(red_team, blue_team, gold_ml_df, df, dmg_weight_dict)
    print('chart_end')
    temp_chart_code = [
        blue_duo_chart,
        blue_count_chart,
        red_duo_chart,
        red_count_chart,
        utils.create_power_graph(blue_power_graph), # create_power_graph는 그래프 객체를 생성하는 함수라고 가정
        utils.create_power_graph(red_power_graph),
        utils.dmg_weight_chart(blue_dmg_weight_data),
        utils.dmg_weight_chart(red_dmg_weight_data),
        blue_dmg_dist_chart,
        red_dmg_dist_chart,
    ]

    comment_code = [
        blue_duo_comment,
        blue_count_comment,
        red_duo_comment,
        red_count_comment,
        blue_gold_comment_code,
        red_gold_comment_code,
        blue_dmg_weight_comment,
        red_dmg_weight_comment,
        blue_dmg_dist_comment,
        red_dmg_dist_comment,
    ]


    context = {
        'champions': selected_champions,
        'stats': stats,
        'temp_chart_code': temp_chart_code,
        'comment_code': comment_code,
        "value": result_df
    }
    return render(request, 'mainapp/report.html', context)
