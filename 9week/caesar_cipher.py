ALPHABET_COUNT = 26


def caesar_cipher_decode(target_text):
    decoded_texts = []

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

        decoded_texts.append(decoded_text)
        print("shift", shift)
        print(decoded_text)
        print()

    return decoded_texts


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


def select_shift(decoded_texts):
    # 눈으로 확인한 자리수를 입력받는다.
    while True:
        selected_shift = input("해독된 자리수를 입력하세요(0-25): ")

        try:
            selected_shift = int(selected_shift)
        except ValueError:
            print("숫자를 입력해 주세요.")
            continue

        if 0 <= selected_shift < ALPHABET_COUNT:
            return selected_shift

        print("0부터 25 사이의 숫자를 입력해 주세요.")


def main():
    password_text = read_password_file()

    if password_text is None:
        return

    decoded_texts = caesar_cipher_decode(password_text)
    selected_shift = select_shift(decoded_texts)
    save_result_file(decoded_texts[selected_shift])


if __name__ == "__main__":
    main()
