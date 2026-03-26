# 파일 읽기
def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # ,로 구분해서 배열로 저장
        data = []
        for line in lines:
            line = line.strip() # 앞뒤 공백 제거
            if line: 
                row = line.split(',') # 행 전체를 , 기준으로 구분
                data.append(row) # 행을 목록에 저장

        return data

    except FileNotFoundError:
        print('파일을 찾을 수 없습니다.')
        return []
    except PermissionError:
        print('접근 권한이 없습니다.')
        return []
    except UnicodeDecodeError:
        print('파일 인코딩 오류 발생')
        return []
    except Exception as e:
        print(f'알 수 없는 오류: {e}')
        return []


# csv로 저장
def save_csv(file_path, header, rows):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(','.join(header) + '\n') # 헤더 리스트를 , 기준으로 이어서 한줄로 합침
            for row in rows:
                file.write(','.join(row) + '\n') # 각 행의 값을 , 기준으로 이어서 한줄로 합침
    except Exception as e:
        print(f'CSV 저장 오류: {e}')

# 파일 내용을 이진 형태로 저장
def write_string(file, text):
    encoded = text.encode('utf-8')
    file.write(len(encoded).to_bytes(4, 'little'))
    file.write(encoded)

# 이진 형태의 파일을 읽어서 utf-8로 디코드
def read_string(file):
    length_data = file.read(4)
    if len(length_data) < 4:
        raise EOFError('이진 파일 읽기 중 예기치 않은 종료가 발생했습니다.')

    length = int.from_bytes(length_data, 'little')
    data = file.read(length)
    if len(data) < length:
        raise EOFError('이진 파일 읽기 중 예기치 않은 종료가 발생했습니다.')

    return data.decode('utf-8')

# 이진 파일을 
def save_bin(file_path, header, rows):
    try:
        with open(file_path, 'wb') as file:
            file.write(len(header).to_bytes(4, 'little'))
            for column in header:
                write_string(file, column)

            file.write(len(rows).to_bytes(4, 'little'))
            for row in rows:
                file.write(len(row).to_bytes(4, 'little'))
                for item in row:
                    write_string(file, item)
    except Exception as e:
        print(f'이진 파일 저장 오류: {e}')


def load_bin(file_path):
    try:
        with open(file_path, 'rb') as file:
            header_count_data = file.read(4)
            if len(header_count_data) < 4:
                return [], []

            header_count = int.from_bytes(header_count_data, 'little')
            header = []
            for _ in range(header_count):
                header.append(read_string(file))

            row_count_data = file.read(4)
            if len(row_count_data) < 4:
                return header, []

            row_count = int.from_bytes(row_count_data, 'little')
            rows = []
            for _ in range(row_count):
                column_count_data = file.read(4)
                if len(column_count_data) < 4:
                    raise EOFError('이진 파일 읽기 중 예기치 않은 종료가 발생했습니다.')

                column_count = int.from_bytes(column_count_data, 'little')
                row = []
                for _ in range(column_count):
                    row.append(read_string(file))
                rows.append(row)

            return header, rows
    except FileNotFoundError:
        print('이진 파일을 찾을 수 없습니다.')
        return [], []
    except PermissionError:
        print('이진 파일 접근 권한이 없습니다.')
        return [], []
    except UnicodeDecodeError:
        print('이진 파일 인코딩 오류 발생')
        return [], []
    except EOFError as e:
        print(f'이진 파일 형식 오류: {e}')
        return [], []
    except Exception as e:
        print(f'이진 파일 읽기 오류: {e}')
        return [], []



def main():
    file_path = '3week/Mars_Base_Inventory_List.csv'
    data = read_file(file_path)

    if not data:
        return

    header = data[0]
    rows = data[1:]

    rows.sort(key=lambda x: float(x[4]), reverse=True)

    # 인화성이 있는 4번째 행 중 0.7 이상인 값들만 리스트에 저장
    danger_items = []
    for row in rows:
        if float(row[4]) >= 0.7:
            danger_items.append(row)

    # 출력
    print('적재 화물 목록(인화성이 높은 순)')
    print(header)
    for row in rows:
        print(row)

    print('\n인화성 지수 0.7 이상 목록')
    print(header)
    for row in danger_items:
        print(row)

    save_csv('3week/Mars_Base_Inventory_danger.csv', header, danger_items)
    bin_file_path = '3week/Mars_Base_Inventory_List.bin'
    save_bin(bin_file_path, header, rows)

    print('\n이진 파일에서 다시 읽은 내용')
    loaded_header, loaded_rows = load_bin(bin_file_path)
    if loaded_header:
        print(loaded_header)
        for row in loaded_rows:
            print(row)


if __name__ == '__main__':
    main()