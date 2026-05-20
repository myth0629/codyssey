ALPHABET_COUNT = 26

# 분석을 멈추기 위한 텍스트 사전 정의
DICTIONARY = ["mars", "base", "password", "system", "secret", "danger", "login"]

def caesar_cipher_decode(target_text):
    # 자리수를 0부터 알파벳 개수만큼 바꾸며 해독한다.
    for shift in range(ALPHABET_COUNT):
        decoded_text = ""

        for char in target_text:
            if "A" <= char <= "Z":
                decoded_text += chr((ord(char) - ord("A") - shift) % ALPHABET_COUNT + ord("A"))
            elif "a" <= char <= "z":
                decoded_text += chr((ord(char) - ord("a") - shift) % ALPHABET_COUNT + ord("a"))
            else:
                decoded_text += char

        print("shift", shift)
        print(decoded_text)
        print()

        # 해독된 텍스트에 사전의 키워드가 포함되어 있는지 확인
        lower_decoded = decoded_text.lower()
        for word in DICTIONARY:
            if word in lower_decoded:
                print(f"사전의 키워드 '{word}'(을)를 발견하여 탐색을 중지합니다. (shift: {shift})")
                return decoded_text
                
    print("사전에 일치하는 단어를 찾을 수 없습니다.")
    return None

def read_password_file():
    # password.txt 파일을 안전하게 읽어온다.
    try:
        with open("password.txt", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print("password.txt 파일을 찾을 수 없습니다.")
    except PermissionError:
        print("password.txt 파일을 읽을 권한이 없습니다.")
    except OSError as error:
        print("password.txt 파일을 읽는 중 오류가 발생했습니다:", error)

    return None


def save_result_file(result_text):
    # 확인한 최종 암호를 result.txt 파일로 저장한다.
    try:
        with open("result.txt", "w", encoding="utf-8") as file:
            file.write(result_text)
        print("result.txt 파일에 저장했습니다.")
    except PermissionError:
        print("result.txt 파일을 저장할 권한이 없습니다.")
    except OSError as error:
        print("result.txt 파일을 저장하는 중 오류가 발생했습니다:", error)


def main():
    password_text = read_password_file()

    if password_text is None:
        return

    decoded_text = caesar_cipher_decode(password_text)
    
    if decoded_text:
        save_result_file(decoded_text)

if __name__ == "__main__":
    main()
