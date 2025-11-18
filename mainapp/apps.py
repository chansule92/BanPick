from django.apps import AppConfig
import pandas as pd
import logging
import joblib
import os
from django.conf import settings

logger = logging.getLogger(__name__)

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainapp'
    # 데이터프레임을 저장할 전역 변수를 MainappConfig 클래스 레벨에서 정의
    # (views.py에서도 이 변수를 import하여 사용하게 됩니다.)
    global_df = {}
    ml_model = None

    def ready(self):
        # 서버 시작 시 딱 한 번만 실행됩니다.
        logger.info("Starting data pre-loading for mainapp...")
        logger.warning("---  App Ready Function Started ---")

        try:

            DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
            MODEL_PATH = os.path.join(DATA_DIR, 'model.pkl')
            logger.warning("---  Starting to load df.csv ---")
            global df
            df = pd.read_csv(os.path.join(DATA_DIR, 'df.csv'))
            logger.warning("---  df.csv Loaded Successfully ---")
            df.columns = df.columns.str.strip()

            logger.warning("---  Starting to load dmg_rate_df.csv ---")
            global dmg_rate_df
            dmg_rate_df = pd.read_csv(os.path.join(DATA_DIR, 'dmg_rate_df.csv'))
            logger.warning("---  dmg_rate_df.csv Loaded Successfully ---")
            dmg_rate_df.columns = dmg_rate_df.columns.str.strip()

            logger.warning("---  Starting to load gold_ml_df.csv ---")
            global gold_ml_df
            gold_ml_df = pd.read_csv(os.path.join(DATA_DIR, 'gold_ml_df.csv'))
            logger.warning("---  gold_ml_df.csv Loaded Successfully ---")
            gold_ml_df.columns = gold_ml_df.columns.str.strip()

            logger.warning("---  Starting to load power_df.csv ---")
            global power_df
            power_df = pd.read_csv(os.path.join(DATA_DIR, 'power_df.csv'))
            logger.warning("---  power_df.csv Loaded Successfully ---")
            power_df.columns = power_df.columns.str.strip()
            power_df.set_index('Champion', inplace=True)

            logger.warning("---  Starting to load result.pkl ---")
            global result
            result = joblib.load(os.path.join(DATA_DIR, 'result.pkl'))
            logger.warning("---  result.pkl Loaded Successfully ---")

            logger.warning(f"Loading pre-trained ML model from: {MODEL_PATH}")
            MainappConfig.ml_model = joblib.load(MODEL_PATH)
            logger.warning("ML Model Loaded and Cached. Server ready for service.")

            MainappConfig.dmg_weight_dict = dmg_rate_df.set_index('Champion')[
                ['deal_norm_total', 'tank_norm_total']
            ].T.to_dict('list')
            logger.warning("Optimized dmg_weight_dict created successfully.")

                # 최종 결과 저장 (예시)
            MainappConfig.global_df['df'] = df
            MainappConfig.global_df['dmg_rate_df'] = dmg_rate_df
            MainappConfig.global_df['power_df'] = power_df
            MainappConfig.global_df['gold_ml_df'] = gold_ml_df

            logger.warning("Data pre-loading complete and cached.")

        except Exception as e:
            logger.error(f"Error during data pre-loading: {e}")
            # DB 연결 실패 등의 예외 처리를 위해 로그를 남깁니다.
