def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

            # 시간 기준 역순 정렬 (각 줄이 시간으로 시작한다고 가정)
            lines.sort(reverse=True)

            for line in lines:
                print(line.strip())

            return lines
        
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
        # 전체 로그 저장
        with open("log_analysis.md", "w", encoding="utf-8") as f:
            f.writelines(content if content else [])

        # 문제 있는 로그 필터링
        problem_lines = [line for line in content if "explosion" in line or "WARN" in line]

        with open("log_problems.md", "w", encoding="utf-8") as f:
            f.writelines(problem_lines)

    except Exception as e:
        print(f"파일 작성 오류: {e}")

def main():
    file_path = '3week/'
    content = read_file(file_path)
    create_markdown(content)

# 직접 실행 시에만 실행 허용
if __name__ == '__main__':
    main()
