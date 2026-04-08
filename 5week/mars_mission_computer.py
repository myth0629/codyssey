import json
import time
import threading

from dummy_sensor import DummySensor


class MissionComputer:
    def __init__(self):
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

    def _listen_for_stop(self):
        try:
            input()
            self.stop_event.set()
        except EOFError:
            return

    def _print_average_values(self, samples):
        average_values = {
            "mars_base_internal_temperature": sum(item["mars_base_internal_temperature"] for item in samples) / len(samples),
            "mars_base_external_temperature": sum(item["mars_base_external_temperature"] for item in samples) / len(samples),
            "mars_base_internal_humidity": sum(item["mars_base_internal_humidity"] for item in samples) / len(samples),
            "mars_base_external_illuminance": sum(item["mars_base_external_illuminance"] for item in samples) / len(samples),
            "mars_base_internal_co2": sum(item["mars_base_internal_co2"] for item in samples) / len(samples),
            "mars_base_internal_oxygen": sum(item["mars_base_internal_oxygen"] for item in samples) / len(samples),
        }

        print(json.dumps(average_values, indent=4, ensure_ascii=False))

    def get_sensor_data(self):
        stop_listener = threading.Thread(target=self._listen_for_stop, daemon=True)
        stop_listener.start()

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

            print(json.dumps(self.env_values, indent=4, ensure_ascii=False))
            samples.append(self.env_values.copy())

            current_time = time.time()
            if current_time - last_average_time >= average_interval and samples:
                self._print_average_values(samples)
                samples = []
                last_average_time = current_time

            if self.stop_event.wait(5):
                print("Sytem stopped....")
                return


RunComputer = MissionComputer()
RunComputer.get_sensor_data()