import zipfile
import itertools
import string
import time
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

def check_password_range(zip_file_path, target_file, first_char):
    """
    첫 번째 글자(first_char)가 고정된 상태로 나머지 5자리의 조합을 검사하는 프로세스용 함수
    """
    charset = string.digits + string.ascii_lowercase
    charset_bytes = [bytes([ord(c)]) for c in charset]
    first_char_byte = bytes([ord(first_char)])
    
    count = 0
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            # 나머지 5자리에 대한 순열 조합
            for pwd_tuple in itertools.product(charset_bytes, repeat=5):
                count += 1
                pwd_bytes = first_char_byte + b''.join(pwd_tuple)
                
                try:
                    # 파일 읽기를 시도하여 패스워드 맞는지 확인
                    zf.read(target_file, pwd=pwd_bytes)
                    # 성공하면 비밀번호 문자열과 시도 횟수 반환
                    return (pwd_bytes.decode('utf-8'), count)
                except RuntimeError as e:
                    if 'Bad password' in str(e) or 'bad password' in str(e):
                        continue
                except Exception:
                    continue
                    
    except Exception:
        pass
    
    # 실패한 경우
    return (None, count)

def unlock_zip(zip_file_path):
    start_time = time.time()
    
    print(f"[시작] 병렬 처리 암호 해독 시작: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    print("시스템의 모든 CPU 코어를 사용하여 탐색을 시작합니다...\n")
    
    if not os.path.exists(zip_file_path):
        print(f"오류: '{zip_file_path}' 파일을 찾을 수 없습니다.")
        return

    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            if not zf.namelist():
                print("오류: ZIP 파일 내부에 파일이 없습니다.")
                return
            target_file = zf.namelist()[0]
    except zipfile.BadZipFile:
        print("오류: 유효한 ZIP 파일이 아닙니다.")
        return

    # 숫자(10) + 소문자(26) = 36개의 첫 글자를 기준으로 36개의 작업 생성
    first_chars = string.digits + string.ascii_lowercase
    total_count = 0
    found_password = None

    # 멀티프로세싱 풀 생성
    with ProcessPoolExecutor() as executor:
        # 각 프로세스에 작업 분배
        futures = {
            executor.submit(check_password_range, zip_file_path, target_file, char): char 
            for char in first_chars
        }
        
        # 완료되는 작업이 있을 때마다 확인
        for future in as_completed(futures):
            char = futures[future]
            try:
                pwd_str, count = future.result()
                total_count += count
                
                if pwd_str:
                    found_password = pwd_str
                    elapsed = time.time() - start_time
                    print(f"\n[성공] 암호를 성공적으로 찾았습니다: '{found_password}'")
                    print(f"총 소요 시간: {elapsed:.2f}초 (진행된 시도 횟수: {total_count}회)")
                    
                    # 진행 중인 다른 프로세스들의 실행 취소
                    for f in futures:
                        f.cancel()
                    break
                else:
                    print(f"진행상황: '{char}'(으)로 시작하는 조합 검사 완료 (총 완료 횟수 누적 중)")
                    
            except Exception as e:
                print(f"오류: 프로세스 실행 중 예외 발생 ({e})")

    if found_password:
        try:
            dir_path = os.path.dirname(os.path.abspath(__file__))
            save_path = os.path.join(dir_path, "password.txt")
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(found_password)
            print(f"암호를 성공적으로 '{save_path}'에 저장했습니다.")
        except Exception as e:
            print(f"오류: password.txt 파일 저장에 실패했습니다. ({e})")
    else:
        print("\n[완료] 모든 조합을 시도했지만 암호를 찾지 못했습니다.")

if __name__ == "__main__":
    target_zip = "emergency_storage_key.zip"
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, target_zip)
    
    if not os.path.exists(zip_path):
        parent_dir = os.path.dirname(base_dir)
        zip_path = os.path.join(parent_dir, target_zip)
        
    unlock_zip(zip_path)
