# mainapp/apps.py

from django.apps import AppConfig
import pandas as pd
from django.db import connection
import logging
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, roc_auc_score

logger = logging.getLogger(__name__)

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainapp'
    # 데이터프레임을 저장할 전역 변수를 MainappConfig 클래스 레벨에서 정의
    # (views.py에서도 이 변수를 import하여 사용하게 됩니다.)
    global_df = {} 

    def ready(self):
        # 서버 시작 시 딱 한 번만 실행됩니다.
        logger.info("Starting data pre-loading for mainapp...")

        try:

          game_list_query ="""SELECT Game_ID,Blue_Result, Red_Result
           FROM banpick.a_game
          WHERE Ver like 'v15%'"""

          game_list_df = pd.read_sql(game_list_query, connection)


          game_list=game_list_df['game_id'].to_list()
          Team_div = ['BLUE','RED']
          Position_div = ['TOP','JUNGLE','MID','ADC','SUPPORT']
          result={}
          for i in game_list:
             team_id={}
             for j in Team_div:
                 temp_list=[]
                 if j =='BLUE':
                     game_result=game_list_df[game_list_df['game_id']==i]['blue_result'].values[0]
                 else :
                     game_result=game_list_df[game_list_df['game_id']==i]['red_result'].values[0]
                 for k in Position_div:
                     champ_query="""SELECT Champion FROM banpick.a_game_stat where Game_ID = '{}' and Team_Div = '{}' and Role = '{}';""".format(i,j,k)
                     champ_df=pd.read_sql(champ_query, connection)
                     temp_list.append((champ_df['champion'].values)[0])
                     team_id[j]=[temp_list,game_result]
                     result[i]=team_id
          query = """
          SELECT M1.Champion
              , M1.con_champ
              , MAX(M1.BP) AS BP
              , MAX(M1.Ban) AS Ban
              , MAX(M1.Pick) AS Pick
              , MAX(M1.total_WIN_rate) AS WIN_rate
              , CASE WHEN MAX(M1.duo_score) = 0 THEN min(M1.duo_score) ELSE Max(M1.duo_score) end AS Duo_Score
              , CASE WHEN MAX(M1.count_score) = 0 THEN Min(M1.count_score) ELSE max(M1.count_score) END AS Count_Score
           FROM ( SELECT M.Champion
                       , M.con_champ
                       , M.Team_YN
                       , M.BP
                       , M.Ban
                       , M.Pick
                       , M.total_WIN_cnt
                       , M.total_WIN_rate
                       , M.duo_play_cnt
                       , M.duo_WIN_cnt
                       , M.duo_WIN_rate
                       , CASE WHEN Team_YN = 'Y' THEN M.duo_WIN_rate - M.total_WIN_rate ELSE 0 END AS duo_score
                       , CASE WHEN Team_YN = 'N' THEN M.duo_WIN_rate - M.total_WIN_rate ELSE 0 END AS count_score
                    FROM ( SELECT T1.Champion
                                , T2.con_champ
                                , T2.Team_YN
                                , T1.BP
                                , T1.Ban
                                , T1.Pick
                                , COALESCE(T3.WIN_cnt,0) AS total_WIN_cnt
                                , CASE WHEN T1.Pick = 0 THEN 0 ELSE ROUND(COALESCE(CAST(T3.WIN_cnt AS NUMERIC),0)/T1.Pick*100,2) END AS total_WIN_rate
                                , COALESCE(T2.play_cnt,0) AS duo_play_cnt
                                , COALESCE(T2.WIN_cnt,0) AS duo_WIN_cnt
                                , CASE WHEN T2.play_cnt = 0 THEN 0 ELSE ROUND(COALESCE(CAST(T2.WIN_cnt AS NUMERIC),0)/COALESCE(T2.play_cnt,0)*100,2) END AS duo_WIN_rate
                             FROM ( SELECT Champion
                                         , count(Champion) AS BP
                                         , SUM(CASE WHEN BP_DIV = 'Ban' THEN 1 ELSE 0 END) AS Ban
                                         , SUM(CASE WHEN BP_DIV = 'Pick' THEN 1 ELSE 0 END) AS Pick
                                      FROM ( SELECT 'Ban' AS BP_DIV
                                                   , Ban AS Champion
                                                FROM banpick.a_game_ban A
                                                     INNER JOIN banpick.a_game B
                                                  ON A.Game_ID = B.Game_ID
                                               WHERE B.Ver like 'v15%'
                                               UNION ALL
                                              SELECT 'Pick' AS BP_DIV
                                                   , Pick AS Champion
                                                FROM banpick.a_game_ban A
                                                     INNER JOIN banpick.a_game B
                                                  ON A.Game_ID = B.Game_ID
                                               WHERE B.Ver like 'v15%'
                                           ) A
                                     GROUP BY Champion
                                  ) T1
                                  LEFT OUTER JOIN
                                  ( SELECT A.Champion AS stan_champ
                                         , B.Champion AS con_champ
                                         , CASE WHEN A.Team_Div = B.Team_Div THEN 'Y' ELSE 'N' END AS Team_YN
                                         , count(DISTINCT A.Game_ID) AS play_cnt
                                         , count(DISTINCT CASE WHEN A.RESULT = 'WIN' THEN A.Game_ID ELSE NULL END) AS WIN_cnt
                                      FROM ( SELECT A.Game_ID
                                                  , A.Champion
                                                  , A.Team_Div
                                                  , CASE WHEN A.Team_Div = 'BLUE' THEN Blue_Result ELSE Red_Result END AS Result
                                               FROM banpick.a_game_stat A
                                                    INNER JOIN banpick.a_game B
                                                 ON A.Game_ID = B.Game_ID
                                              WHERE B.Ver like 'v15%'
                                           ) A
                                           LEFT OUTER JOIN
                                           ( SELECT A.Game_ID
                                                  , A.Champion
                                                  , A.Team_Div
                                                  , CASE WHEN A.Team_Div = 'BLUE' THEN Blue_Result ELSE Red_Result END AS Result
                                               FROM banpick.a_game_stat A
                                                    INNER JOIN banpick.a_game B
                                                 ON A.Game_ID = B.Game_ID
                                              WHERE B.Ver like 'v15%'
                                           ) B
                                        ON A.Game_ID = B.Game_ID
                                       AND A.Champion != B.Champion
                                     GROUP BY A.Champion
                                         , B.Champion
                                         , CASE WHEN A.Team_Div = B.Team_Div THEN 'Y' ELSE 'N' END
                                  ) T2
                               ON T1.Champion = T2.stan_Champ
                                  LEFT OUTER JOIN
                                  ( SELECT A.Champion
                                         , sum(CASE WHEN A.Team_Div = 'BLUE' AND B.Blue_Result = 'WIN' THEN 1
                                                    WHEN A.Team_Div = 'RED' AND B.Red_result = 'WIN' THEN 1 ELSE 0 END) AS WIN_cnt
                                      FROM banpick.a_game_stat A
                                           INNER JOIN banpick.a_game B
                                        ON A.Game_ID = B.Game_ID
                                     WHERE B.Ver like 'v15%'
                                     GROUP BY A.Champion
                                  ) T3
                               ON T1.Champion = T3.Champion
                         ) M
                   WHERE 1=1
                     /* AND duo_play_cnt > 2
                     AND BP > 9 */
                ) M1
          GROUP BY M1.Champion
               , M1.con_champ
          """
          df = pd.read_sql(query.replace('\n',' '), connection)
          df['champion'] = df['champion'].str.lower()
          df['con_champ'] = df['con_champ'].str.lower()

          query2="""SELECT B.Champion
              , A.Gold_Data
              , A.CS_Data
           FROM banpick.a_game_timeline A
                INNER JOIN banpick.a_game_stat B
             ON A.game_ID = B.Game_ID
            AND A.Team_Div = B.Team_Div
            AND A.ROLE = B.Role
            WHERE A.Game_ID IN (SELECT game_ID FROM banpick.a_game WHERE Ver like 'v15%') """
          df2 = pd.read_sql(query2, connection)
          df2['champion'] = df2['champion'].str.lower()

          query3="""
          SELECT F.Champion
              , F.avg_dpm * Ad_rate AS AD_p
              , F.avg_dpm * AP_rate AS AP_p
              , F.avg_dpm * TD_rate AS TD_p
              , F.avg_dpm
              , F.tank_death
              , F.tank_time
              , F.deal_death
              , F.deal_time
           FROM ( SELECT CASE WHEN A.ROLE = 'SUPPORT' THEN concat(A.Champion,'_',A.ROLE) ELSE A.Champion end AS Champion
                       , round(avg(A.DPM),2) AS avg_dpm
                       , round(SUM(A."Physical Damage") / SUM(A."Total damage to Champion"),2) AS AD_rate
                       , round(SUM(A."Magic Damage") / SUM(A."Total damage to Champion") ,2) AS AP_rate
                       , round(SUM(A."True Damage") / SUM(A."Total damage to Champion") ,2) AS TD_rate
                       , SUM(CASE WHEN A.ROLE = 'JUNGLE' THEN A."Total damage taken" * 0.7 ELSE A."Total damage taken" END) / (SUM(A.Deaths) + count(A.Champion))  AS tank_death
                       , avg(ROUND(CASE WHEN A.ROLE = 'JUNGLE' THEN A."Total damage taken" * 0.7 ELSE A."Total damage taken" END / ROUND((CAST(LEFT(B.Game_Time,2) AS NUMERIC)*60 + CAST(RIGHT(B.Game_Time,2) AS NUMERIC)) / 60,2))) AS tank_time
                       , SUM(A."Total damage to Champion") / (SUM(A.Deaths) + count(A.Champion))  AS deal_death
                       , round(avg(A.DPM),2) AS deal_time
                    FROM banpick.a_game_stat A
                         INNER JOIN banpick.a_game B
                      ON A.Game_ID = B.Game_ID 
                   WHERE B.Ver like 'v15%'
                   GROUP BY CASE WHEN A.ROLE = 'SUPPORT' THEN concat(A.Champion,'_',A.ROLE) ELSE A.Champion end
                ) F

          """
          sql2 = """
          SELECT A.Game_ID 
              , B.Champion 
              , B.Team_Div 
              , B.Role
              , A.Blue_Result 
              , A.Red_Result 
           FROM banpick.a_game A
                INNER JOIN 
                banpick.a_game_stat B
             ON A.Game_ID = B.Game_ID 
          WHERE A.Ver like 'v15%'
          """
          dmg_rate_df=pd.read_sql_query(query3,connection)
          dmg_rate_df['champion'] = dmg_rate_df['champion'].str.lower()
          avg_tank_death = dmg_rate_df['tank_death'].sum()/dmg_rate_df['tank_death'].count()
          avg_tank_time = dmg_rate_df['tank_time'].sum()/dmg_rate_df['tank_time'].count()
          dmg_rate_df['tank_death_norm']=dmg_rate_df['tank_death']/avg_tank_death
          dmg_rate_df['tank_time_norm']=dmg_rate_df['tank_time']/avg_tank_time
          dmg_rate_df['tank_norm_total'] = dmg_rate_df['tank_death_norm'] + dmg_rate_df['tank_time_norm']
          avg_deal_death = dmg_rate_df['deal_death'].sum()/dmg_rate_df['deal_death'].count()
          avg_deal_time = dmg_rate_df['deal_time'].sum()/dmg_rate_df['deal_time'].count()
          dmg_rate_df['deal_death_norm']=dmg_rate_df['deal_death']/avg_deal_death
          dmg_rate_df['deal_time_norm']=dmg_rate_df['deal_time']/avg_deal_time
          dmg_rate_df['deal_norm_total'] = dmg_rate_df['deal_death_norm'] + dmg_rate_df['deal_time_norm']
          dmg_rate_df['Champion']=dmg_rate_df['Champion'].str.lower()

          cham_powergraph=[]
          champion_list=df2['champion'].unique()
          for cham in champion_list:
             gold_df=df2[df2['champion']==cham]
             time_gold=[]
             for i in gold_df['gold_data']:
                 data=eval(i)
                 temp_list=[]
                 for j in range(0,len(data)-1):
                     if j != 0:
                         temp_list.append(int(data[j])-int(data[j-1]))
                 time_gold.append(temp_list)
             power_graph=[]
             for k in range(0,30):
                 temp=[]
                 value=0
                 for u in time_gold:
                     try:
                         temp.append(u[k])
                     except:
                         pass
                 if len(temp) != 0:
                     value=round(sum(temp)/len(temp),2)
                 power_graph.append(value)
             cham_powergraph.append([cham,power_graph])
          power_df=pd.DataFrame(cham_powergraph)
          power_df.columns = ['champion','gold_data']

          edu_ml=[]
          for i in game_list:
             sample_ml=[]
             sample=''
             blue_gold=gold(result[i]['BLUE'][0])
             red_gold=gold(result[i]['RED'][0])
             sample=pd.concat([blue_gold,red_gold],axis=1)
             sample.columns=['Time','blue_gold','-','red_gold']
             sample['diff_gold']=sample['blue_gold']-sample['red_gold']
          #    sample_ml.append(round(sample[sample['Time']=='early']['diff_gold'].iloc[0],2))
             sample_ml.append(round(sample[sample['Time']=='middle']['diff_gold'].iloc[0],2))
             try:
                 sample_ml.append(round(sample[sample['Time']=='late']['diff_gold'].iloc[0],2))
             except:
                 sample_ml.append(0)
             edu_ml.append(sample_ml)
          gold_ml_df=pd.DataFrame(edu_ml)
          gold_ml_df.columns = ['middle_gold','late_gold']
          gold_ml_df
          ml_df=[]
          for i in game_list:
             ml_temp_df=ml_features(result[i]['BLUE'][0],result[i]['RED'][0])
             if result[i]['BLUE'][1] == 'WIN':
                 ml_game_result=[1]
             else:
                 ml_game_result=[0]
             ml_temp_df2=pd.DataFrame(ml_game_result)    
             ml_temp_df2.columns=['game_result']
             ml_temp_df3=pd.concat([ml_temp_df,ml_temp_df2],axis=1)
             if len(ml_df)==0:
                 ml_df=ml_temp_df3
             else:
                 ml_df=pd.concat([ml_df,ml_temp_df3],axis=0)
          features=ml_df[['comb_score','over_atk','over_def','atk_cnt','def_cnt','gold']]
          features_result=ml_df[['game_result']]
          X= features
          y= features_result
          params = {
             'objective': 'binary:logistic',  # 이진 분류
             'eval_metric': 'logloss',        # 평가 지표
             'max_depth': 3,
             'eta': 0.05,
             'gamma': 1,
             'min_child_weight':3,
             'subsample': 0.8,
             'colsample_bytree': 0.8,
             'seed': 42,
             'verbosity': 0
          }

          # (3) KFold 설정
          kf = KFold(n_splits=5, shuffle=True, random_state=42)

          # (4) 교차검증 수행
          fold = 1
          acc_scores = []
          auc_scores = []

          for train_idx, val_idx in kf.split(X):
             X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
             y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
             
             model = xgb.XGBClassifier(n_estimators=200)
             calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=5)
             calibrated_model.fit(X_train, y_train,
                       eval_set=[(X_val, y_val)],
                       verbose=False)
               
             y_pred = calibrated_model.predict(X_val)
             y_pred_prob = calibrated_model.predict_proba(X_val)[:, 1]
             
             acc = accuracy_score(y_val, y_pred)
             auc = roc_auc_score(y_val, y_pred_prob)
             
             print(f"Fold {fold} | Accuracy: {acc:.4f} | AUC: {auc:.4f}")
             acc_scores.append(acc)
             auc_scores.append(auc)
             fold += 1
          # (5) 최종 평균 성능
          print("\n==== 최종 평균 성능 ====")
          print(f"Average Accuracy: {np.mean(acc_scores):.4f}")
          print(f"Average AUC: {np.mean(auc_scores):.4f}")
          final_model = xgb.XGBClassifier(n_estimators=100, **params)
          final_model.fit(X, y)
            
            # 최종 결과 저장 (예시)
          MainappConfig.global_df['df'] = df
          MainappConfig.global_df['df2'] = df2
          MainappConfig.global_df['dmg_rate_df'] = dmg_rate_df
          MainappConfig.global_df['power_df'] = power_df
          MainappConfig.global_df['gold_ml_df'] = gold_ml_df

            
          logger.info("Data pre-loading complete and cached.")

        except Exception as e:
            logger.error(f"Error during data pre-loading: {e}")
            # DB 연결 실패 등의 예외 처리를 위해 로그를 남깁니다.
