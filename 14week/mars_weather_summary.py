import csv
import os
import struct
import zlib
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

try:
    from mysql import connector
except ImportError:
    connector = None


CSV_FILE_NAME = 'mars_weathers_data.CSV'
OUTPUT_FILE_NAME = 'mars_weather_summary.png'
IMAGE_WIDTH = 1000
IMAGE_HEIGHT = 600
IMAGE_MARGIN = 60


class MySQLHelper:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ) -> None:
        self.connection = connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )

    def execute(
        self,
        query: str,
        values: tuple[Any, ...] | None = None,
    ) -> None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, values)
        finally:
            cursor.close()

    def fetch_all(
        self,
        query: str,
        values: tuple[Any, ...] | None = None,
    ) -> list[tuple[Any, ...]]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, values)
            return cursor.fetchall()
        finally:
            cursor.close()

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def close(self) -> None:
        if self.connection.is_connected():
            self.connection.close()


def read_weather_data(csv_path: Path) -> list[tuple[datetime, int, int]]:
    weather_data = []

    with csv_path.open('r', encoding='utf-8-sig', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {'mars_date', 'temp', 'stom'}

        if reader.fieldnames is None:
            raise ValueError('CSV 파일에 헤더가 없습니다.')

        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            missing_text = ', '.join(sorted(missing_columns))
            raise ValueError(
                f'CSV 필수 컬럼이 없습니다: {missing_text}'
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                mars_date = datetime.fromisoformat(row['mars_date'].strip())
                # INT 컬럼 명세에 맞춰 CSV의 소수 온도를 반올림한다.
                temp = int(
                    Decimal(row['temp']).quantize(
                        Decimal('1'),
                        rounding=ROUND_HALF_UP,
                    )
                )
                storm = int(row['stom'])
            except (AttributeError, TypeError, ValueError) as error:
                raise ValueError(
                    f'CSV {row_number}행의 데이터 형식이 '
                    '올바르지 않습니다.'
                ) from error

            weather_data.append((mars_date, temp, storm))

    return weather_data


def create_weather_table(database: MySQLHelper) -> None:
    # 과제 명세의 기본 키, 자동 증가, 필수 입력 조건을 지정한다.
    database.execute(
        '''
        CREATE TABLE IF NOT EXISTS mars_weather (
            weather_id INT AUTO_INCREMENT PRIMARY KEY,
            mars_date DATETIME NOT NULL,
            temp INT,
            storm INT
        )
        '''
    )
    database.commit()


def insert_weather_data(
    database: MySQLHelper,
    weather_data: list[tuple[datetime, int, int]],
) -> None:
    insert_query = '''
        INSERT INTO mars_weather (mars_date, temp, storm)
        VALUES (%s, %s, %s)
    '''

    try:
        # 반복 실행해도 CSV와 테이블 내용이 같도록 기존 행을 비운다.
        database.execute('TRUNCATE TABLE mars_weather')
        for weather_row in weather_data:
            database.execute(insert_query, weather_row)
        database.commit()
    except Exception:
        database.rollback()
        raise


def get_weather_summary(
    database: MySQLHelper,
) -> tuple[int, float, int, int, int]:
    summary_rows = database.fetch_all(
        '''
        SELECT
            COUNT(*),
            COALESCE(AVG(temp), 0),
            COALESCE(MIN(temp), 0),
            COALESCE(MAX(temp), 0),
            COALESCE(SUM(storm), 0)
        FROM mars_weather
        '''
    )
    count, average_temp, minimum_temp, maximum_temp, storm_count = (
        summary_rows[0]
    )
    return (
        int(count),
        float(average_temp),
        int(minimum_temp),
        int(maximum_temp),
        int(storm_count),
    )


def set_pixel(
    pixels: bytearray,
    x_position: int,
    y_position: int,
    color: tuple[int, int, int],
) -> None:
    if not 0 <= x_position < IMAGE_WIDTH:
        return
    if not 0 <= y_position < IMAGE_HEIGHT:
        return

    pixel_index = (y_position * IMAGE_WIDTH + x_position) * 3
    pixels[pixel_index:pixel_index + 3] = bytes(color)


def draw_line(
    pixels: bytearray,
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    color: tuple[int, int, int],
) -> None:
    x_distance = abs(end_x - start_x)
    y_distance = -abs(end_y - start_y)
    x_step = 1 if start_x < end_x else -1
    y_step = 1 if start_y < end_y else -1
    line_error = x_distance + y_distance

    while True:
        set_pixel(pixels, start_x, start_y, color)
        if start_x == end_x and start_y == end_y:
            break

        doubled_error = line_error * 2
        if doubled_error >= y_distance:
            line_error += y_distance
            start_x += x_step
        if doubled_error <= x_distance:
            line_error += x_distance
            start_y += y_step


def make_png_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + chunk_data)
    return (
        struct.pack('>I', len(chunk_data))
        + chunk_type
        + chunk_data
        + struct.pack('>I', checksum)
    )


def save_summary_png(
    output_path: Path,
    weather_rows: list[tuple[Any, ...]],
    summary: tuple[int, float, int, int, int],
) -> None:
    pixels = bytearray([245, 247, 250] * IMAGE_WIDTH * IMAGE_HEIGHT)
    chart_left = IMAGE_MARGIN
    chart_top = IMAGE_MARGIN
    chart_right = IMAGE_WIDTH - IMAGE_MARGIN
    chart_bottom = IMAGE_HEIGHT - IMAGE_MARGIN

    draw_line(
        pixels,
        chart_left,
        chart_bottom,
        chart_right,
        chart_bottom,
        (70, 80, 95),
    )
    draw_line(
        pixels,
        chart_left,
        chart_top,
        chart_left,
        chart_bottom,
        (70, 80, 95),
    )

    if weather_rows:
        temperatures = [int(row[1]) for row in weather_rows]
        minimum_temp = min(temperatures)
        maximum_temp = max(temperatures)
        temperature_range = max(maximum_temp - minimum_temp, 1)
        maximum_storm = max(int(row[2]) for row in weather_rows)
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        previous_temp_point = None
        previous_storm_point = None

        for index, row in enumerate(weather_rows):
            point_ratio = index / max(len(weather_rows) - 1, 1)
            x_position = chart_left + round(chart_width * point_ratio)
            temp_ratio = (int(row[1]) - minimum_temp) / temperature_range
            temp_y = chart_bottom - round(chart_height * temp_ratio)
            storm_ratio = int(row[2]) / max(maximum_storm, 1)
            storm_y = chart_bottom - round(chart_height * storm_ratio)

            if previous_temp_point is not None:
                draw_line(
                    pixels,
                    previous_temp_point[0],
                    previous_temp_point[1],
                    x_position,
                    temp_y,
                    (35, 105, 190),
                )

            if previous_storm_point is not None:
                draw_line(
                    pixels,
                    previous_storm_point[0],
                    previous_storm_point[1],
                    x_position,
                    storm_y,
                    (220, 65, 65),
                )

            previous_temp_point = (x_position, temp_y)
            previous_storm_point = (x_position, storm_y)

    count, average_temp, minimum_temp, maximum_temp, storm_count = summary
    summary_text = (
        f'count={count}; average_temp={average_temp:.2f}; '
        f'min_temp={minimum_temp}; max_temp={maximum_temp}; '
        f'storm_count={storm_count}'
    ).encode('latin-1')

    raw_image = bytearray()
    row_size = IMAGE_WIDTH * 3
    for row_index in range(IMAGE_HEIGHT):
        row_start = row_index * row_size
        raw_image.append(0)
        raw_image.extend(pixels[row_start:row_start + row_size])

    png_data = bytearray(b'\x89PNG\r\n\x1a\n')
    png_data.extend(
        make_png_chunk(
            b'IHDR',
            struct.pack(
                '>IIBBBBB',
                IMAGE_WIDTH,
                IMAGE_HEIGHT,
                8,
                2,
                0,
                0,
                0,
            ),
        )
    )
    png_data.extend(
        make_png_chunk(b'tEXt', b'Description\x00' + summary_text)
    )
    png_data.extend(make_png_chunk(b'IDAT', zlib.compress(raw_image)))
    png_data.extend(make_png_chunk(b'IEND', b''))
    output_path.write_bytes(png_data)


def print_weather_data(
    weather_data: list[tuple[datetime, int, int]],
) -> None:
    print('mars_date, temp, storm')
    for mars_date, temp, storm in weather_data:
        print(f'{mars_date.isoformat(sep=" ")}, {temp}, {storm}')


def main() -> None:
    if connector is None:
        raise RuntimeError(
            'MySQL 연결을 위해 mysql-connector-python을 '
            '설치해야 합니다.'
        )

    base_directory = Path(__file__).resolve().parent
    csv_path = base_directory / CSV_FILE_NAME
    output_path = base_directory / OUTPUT_FILE_NAME

    if not csv_path.exists():
        raise FileNotFoundError(
            f'CSV 파일을 찾을 수 없습니다: {csv_path}'
        )

    weather_data = read_weather_data(csv_path)
    print_weather_data(weather_data)

    database = MySQLHelper(
        host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
        port=int(os.environ.get('MYSQL_PORT', '3306')),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DATABASE', 'mars'),
    )

    try:
        create_weather_table(database)
        insert_weather_data(database, weather_data)
        weather_rows = database.fetch_all(
            '''
            SELECT mars_date, temp, storm
            FROM mars_weather
            ORDER BY mars_date
            '''
        )
        summary = get_weather_summary(database)
        save_summary_png(output_path, weather_rows, summary)
    finally:
        database.close()

    print(f'{len(weather_data)}개의 날씨 데이터를 저장했습니다.')
    print(f'요약 이미지를 저장했습니다: {output_path}')


if __name__ == '__main__':
    main()
