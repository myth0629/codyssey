print('Hello Mars')

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            print(content)
            return content
        
    except FileNotFoundError:
        print('파일을 찾을 수 없습니다.')
    except PermissionError:
        print('접근 권한이 없습니다.')
    except UnicodeDecodeError:
        print('파일 인코딩 오류 발생')
    except Exception as e:
        print(f'알 수 없는 오류: {e}')

def create_markdown(content):
    try:
        with open("log_analysis.md", "w", encoding="utf-8") as f:
            f.write(content if content else "")
    except Exception as e:
        print(f"파일 작성 오류: {e}")

def main():
    file_path = '1week/mission_computer_main.log'
    content = read_file(file_path)
    create_markdown(content)

# 직접 실행 시에만 실행 허용
if __name__ == '__main__':
    main()
