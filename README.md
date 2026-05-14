# 카이사르 암호 해독기

## 1. 개요 및 동작 방식
카이사르 암호는 문장 내의 모든 알파벳을 일정한 거리(Shift)만큼 밀어서 다른 알파벳으로 바꾸는 암호화 방식입니다. 
본 프로그램은 이 Shift 값이 무엇인지 모른다는 가정하에, 가능한 모든 위치 이동(0~25)을 시도하는 **브루트 포스(Brute-force) 방식**을 사용하여 암호를 해독합니다.

---

## 2. 핵심 로직 분석

### 2.1 암호 해독 알고리즘 (`caesar_cipher_decode`)
```python
def caesar_cipher_decode(target_text):
    decoded_texts = []
    for shift in range(ALPHABET_COUNT):
        decoded_text = ""
        for char in target_text:
            if "A" <= char <= "Z":
                decoded_text += chr((ord(char) - ord("A") - shift) % ALPHABET_COUNT + ord("A"))
            elif "a" <= char <= "z":
                # 소문자 처리 로직 동일
            else:
                decoded_text += char
        decoded_texts.append(decoded_text)
    return decoded_texts
```
- **해석 및 의도**:
  - `ord()`와 `chr()` 함수를 활용해 문자를 아스키코드(숫자)로 변환한 뒤 사칙연산을 수행합니다.
  - **왜 모듈러(`% ALPHABET_COUNT`) 연산을 사용했는가?**: 알파벳 순서를 밀었을 때 'Z'를 넘어가면 다시 'A'로 돌아오게 하는(Wrap-around) 가장 수학적이고 깔끔한 방법입니다. 조건문(`if value > 'Z'`)으로 처리할 수도 있지만, 모듈러 연산을 통해 코드의 복잡성을 낮추고 가독성을 높였습니다.
  - 알파벳이 아닌 문자(공백, 특수기호 등)는 암호화 대상이 아니므로 그대로 유지(`else` 구문)하도록 설계하여 문맥을 파악하기 쉽게 했습니다.

### 2.2 안전한 파일 입출력 및 예외 처리 (`read_password_file`)
```python
def read_password_file():
    try:
        with open("password.txt", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print("password.txt 파일을 찾을 수 없습니다.")
    # PermissionError, OSError 등 예외 처리 생략됨
```
- **해석 및 의도**:
  - `with open(...)` 컨텍스트 매니저를 사용하여 파일을 열었습니다.
  - **왜 이렇게 썼는가?**: 파일 처리는 외부 환경(OS, 디스크 상태, 사용자 권한 등)에 의존하므로 에러 발생 확률이 높습니다. `try-except` 블록을 통하여 `FileNotFoundError`(파일 누락), `PermissionError`(권한 없음) 등을 구체적으로 분기하여 처리했습니다. 이렇게 하면 단순히 프로그램이 크래시(Crash) 나는 것을 방지하고 사용자에게 어떤 문제가 발생했는지 정확한 피드백을 줄 수 있습니다.
  - `with` 문을 사용하면 도중에 에러가 나거나 작업이 끝났을 때 파일 스트림을 확실하게 닫아 메모리 누수를 방지할 수 있습니다.

### 2.3 안정적인 사용자 입력 검증 (`select_shift`)
```python
def select_shift(decoded_texts):
    while True:
        selected_shift = input("해독된 자리수를 입력하세요(0-25): ")
        try:
            selected_shift = int(selected_shift)
        except ValueError:
            print("숫자를 입력해 주세요.")
            continue

        if 0 <= selected_shift < ALPHABET_COUNT:
            return selected_shift
```
- **해석 및 의도**:
  - `while True` 무한 루프 안에서 사용자 인터랙션을 받습니다.
  - **왜 이렇게 썼는가?**: 사용자의 입력은 항상 예측 불가능합니다. 문자를 입력하거나 범위(0~25)를 벗어난 숫자를 입력할 경우 프로그램이 종료되지 않도록 `try-except ValueError`로 타입 검증을 수행하고, 논리 연산자(`0 <= selected_shift < ALPHABET_COUNT`)로 범위 검증을 수행합니다. 
  - 올바른 데이터를 입력받을 때까지(Validation) 반복함으로써 프로그램의 불시 종료(Robustness)를 막습니다.

---

## 3. 총평 (Architecture Summary)
- **상수 분리**: `ALPHABET_COUNT = 26`을 하드코딩하지 않고 전역 상수로 정의하여 매직 넘버(Magic Number)를 없앴습니다.
- **모듈화**: 파일 읽기, 암호 해독, 입력 받기, 파일 저장 등의 역할을 각각의 함수로 잘 분기 및 결합하여 단일 책임 원칙(SRP)에 근접하게 설계되었습니다.
