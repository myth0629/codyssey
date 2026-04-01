import os
from datetime import datetime
import random


class DummySensor:
    def __init__(self):
        # 센서가 관리하는 환경 값을 저장할 사전
        self.env_values = {
            'mars_base_internal_temperature': None,
            'mars_base_external_temperature': None,
            'mars_base_internal_humidity': None,
            'mars_base_external_illuminance': None,
            'mars_base_internal_co2': None,
            'mars_base_internal_oxygen': None,
        }

    def set_env(self):
        # 각 항목에 지정된 범위의 랜덤 값을 채운다
        self.env_values['mars_base_internal_temperature'] = random.uniform(18, 30)
        self.env_values['mars_base_external_temperature'] = random.uniform(0, 21)
        self.env_values['mars_base_internal_humidity'] = random.uniform(50, 60)
        self.env_values['mars_base_external_illuminance'] = random.uniform(500, 715)
        self.env_values['mars_base_internal_co2'] = random.uniform(0.02, 0.1)
        self.env_values['mars_base_internal_oxygen'] = random.uniform(4, 7)

    def get_env(self):
        # 현재 저장된 환경 값을 그대로 반환한다
        log_path = os.path.join(os.path.dirname(__file__), 'mars_mission_computer.log')
        log_line = (
            f"{datetime.now():%Y-%m-%d %H:%M:%S}, "
            f"화성 기지 내부 온도: {self.env_values['mars_base_internal_temperature']:.2f}, "
            f"화성 기지 외부 온도: {self.env_values['mars_base_external_temperature']:.2f}, "
            f"화성 기지 내부 습도: {self.env_values['mars_base_internal_humidity']:.2f}, "
            f"화성 기지 외부 광량: {self.env_values['mars_base_external_illuminance']:.2f}, "
            f"화성 기지 내부 이산화탄소 농도: {self.env_values['mars_base_internal_co2']:.2f}, "
            f"화성 기지 내부 산소 농도: {self.env_values['mars_base_internal_oxygen']:.2f}\n"
        )

        with open(log_path, 'a', encoding='utf-8') as file:
            file.write(log_line)

        return self.env_values


# 더미 센서를 생성하고, 값 설정 후 확인한다.
ds = DummySensor()
ds.set_env()
print(ds.get_env())