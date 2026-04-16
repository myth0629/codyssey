import json
import os
import platform
import time
import threading

import psutil

from dummy_sensor import DummySensor


class MissionComputer:
    def __init__(self):
        # 센서 값을 저장할 공간
        self.env_values = {
            "mars_base_internal_temperature": None,
            "mars_base_external_temperature": None,
            "mars_base_internal_humidity": None,
            "mars_base_external_illuminance": None,
            "mars_base_internal_co2": None,
            "mars_base_internal_oxygen": None,
        }

        self.ds = DummySensor()
        self.stop_event = threading.Event()
        self.output_settings = self._load_output_settings()

    def _load_output_settings(self):
        setting_path = os.path.join(os.path.dirname(__file__), "setting.txt")
        settings = {"info": [], "load": []}
        current_section = None

        if not os.path.exists(setting_path):
            return settings

        with open(setting_path, "r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue

                if line.startswith("[") and line.endswith("]"):
                    section_name = line[1:-1].strip().lower()
                    if section_name in ("info", "mission_computer_info"):
                        current_section = "info"
                    elif section_name in ("load", "mission_computer_load"):
                        current_section = "load"
                    else:
                        current_section = None
                    continue

                if current_section in settings:
                    settings[current_section].append(line)

        return settings

    def _select_output_values(self, section, values):
        selected_keys = self.output_settings.get(section, [])
        if not selected_keys:
            return values

        return {key: values.get(key) for key in selected_keys if key in values}

    def _listen_for_stop(self):
        # Enter 입력을 기다렸다가 종료 신호를 보낸다.
        try:
            input()
            self.stop_event.set()
        except EOFError:
            return

    def _print_average_values(self, samples):
        # 5분 동안 모은 값의 평균을 계산한다.
        average_values = {
            "mars_base_internal_temperature": sum(item["mars_base_internal_temperature"] for item in samples) / len(samples),
            "mars_base_external_temperature": sum(item["mars_base_external_temperature"] for item in samples) / len(samples),
            "mars_base_internal_humidity": sum(item["mars_base_internal_humidity"] for item in samples) / len(samples),
            "mars_base_external_illuminance": sum(item["mars_base_external_illuminance"] for item in samples) / len(samples),
            "mars_base_internal_co2": sum(item["mars_base_internal_co2"] for item in samples) / len(samples),
            "mars_base_internal_oxygen": sum(item["mars_base_internal_oxygen"] for item in samples) / len(samples),
        }

        print(json.dumps(average_values, indent=4, ensure_ascii=False))

    def _print_json(self, values):
        print(json.dumps(values, indent=4, ensure_ascii=False))

    def get_mission_computer_info(self):
        system_info = {
            "operating_system": platform.system(),
            "operating_system_version": platform.version(),
            "cpu_type": platform.processor() or platform.machine(),
            "cpu_core_count": os.cpu_count(),
            "memory_size_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        }

        selected_info = self._select_output_values("info", system_info)
        self._print_json(selected_info)
        return selected_info

    def get_mission_computer_load(self):
        mission_computer_load = {
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "memory_usage_percent": psutil.virtual_memory().percent,
        }

        selected_load = self._select_output_values("load", mission_computer_load)
        self._print_json(selected_load)
        return selected_load

    def get_sensor_data(self):
        # 종료 입력 감시는 별도 스레드로 처리
        stop_listener = threading.Thread(target=self._listen_for_stop, daemon=True)
        stop_listener.start()

        # 5분 평균 계산용 샘플 보관
        samples = []
        average_interval = 300
        last_average_time = time.time()

        while True:
            if self.stop_event.is_set():
                print("Sytem stopped....")
                return

            sensor_data = self.ds.get_env_data()

            self.env_values["mars_base_internal_temperature"] = sensor_data.get("mars_base_internal_temperature")
            self.env_values["mars_base_external_temperature"] = sensor_data.get("mars_base_external_temperature")
            self.env_values["mars_base_internal_humidity"] = sensor_data.get("mars_base_internal_humidity")
            self.env_values["mars_base_external_illuminance"] = sensor_data.get("mars_base_external_illuminance")
            self.env_values["mars_base_internal_co2"] = sensor_data.get("mars_base_internal_co2")
            self.env_values["mars_base_internal_oxygen"] = sensor_data.get("mars_base_internal_oxygen")

            # 현재 센서 값을 JSON 형태로 출력한다.
            print(json.dumps(self.env_values, indent=4, ensure_ascii=False))
            samples.append(self.env_values.copy())

            # 5분이 지나면 평균값도 따로 출력한다.
            current_time = time.time()
            if current_time - last_average_time >= average_interval and samples:
                self._print_average_values(samples)
                samples = []
                last_average_time = current_time

            if self.stop_event.wait(5):
                print("Sytem stopped....")
                return


runComputer = MissionComputer()
runComputer.get_mission_computer_info()
runComputer.get_mission_computer_load()