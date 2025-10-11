# mainapp/apps.py

from django.apps import AppConfig
from django.db import connection
import pandas as pd
import numpy as np
import logging
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, roc_auc_score
from . import utils
import joblib
import os
from django.conf import settings # <-- 이 줄을 추가해야 합니다!

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

          DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
        
          global df
          df = pd.read_csv(os.path.join(DATA_DIR, 'df.csv'))
          
          global dmg_rate_df
          dmg_rate_df = pd.read_csv(os.path.join(DATA_DIR, 'dmg_rate_df.csv'))
          
          global gold_ml_df
          gold_ml_df = pd.read_csv(os.path.join(DATA_DIR, 'gold_ml_df.csv'))
          
          global power_df
          power_df = pd.read_csv(os.path.join(DATA_DIR, 'power_df.csv'))
            
          global result
          result = joblib.load(os.path.join(DATA_DIR, 'result.pkl'))
          game_list = list(result.keys())

          ml_df=[]
          for i in game_list:
             ml_temp_df=utils.ml_features(result[i]['BLUE'][0],result[i]['RED'][0],gold_ml_df,df, dmg_rate_df)
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
