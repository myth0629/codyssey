# 카이사르 암호 해독기

`password.txt`에 저장된 카이사르 암호문을 읽고, 가능한 모든 자리 이동값(Shift)으로 해독을 시도한 뒤, 사전에 등록된 키워드가 발견되면 해당 결과를 `result.txt`에 저장하는 프로그램입니다.

## 개요

카이사르 암호는 알파벳을 일정한 칸수만큼 밀어서 다른 문자로 바꾸는 단순 치환 암호입니다.

예를 들어 알파벳을 3칸 밀면 `A`는 `D`, `B`는 `E`가 됩니다. 반대로 해독할 때는 같은 칸수만큼 되돌리면 원문을 얻을 수 있습니다.

이 프로그램은 암호화에 사용된 Shift 값을 모른다는 가정으로 동작합니다. 따라서 `0`부터 `25`까지 모든 Shift 값을 시도하는 브루트 포스 방식으로 해독합니다.

다만 모든 결과를 사람이 직접 고르는 대신, `DICTIONARY`에 등록된 단어가 해독 결과 안에서 발견되면 올바른 문장으로 판단하고 탐색을 중지합니다.

## 파일 구성

- `9week/caesar_cipher.py`: 카이사르 암호 해독 프로그램
- `password.txt`: 해독할 암호문이 들어 있는 입력 파일
- `result.txt`: 사용자가 선택한 최종 해독 결과가 저장되는 출력 파일

## 실행 방법

프로젝트 루트 디렉터리에서 아래 명령어를 실행합니다.

```bash
python 9week/caesar_cipher.py
```

프로그램은 `password.txt`를 읽은 뒤 Shift `0`부터 `25`까지 해독 후보를 순서대로 출력합니다.

해독 결과에서 사전 키워드가 발견되면 탐색을 멈추고, 해당 문장을 `result.txt`에 저장합니다.

## 동작 흐름

1. `password.txt` 파일을 읽습니다.
2. Shift 값을 `0`부터 `25`까지 바꾸며 해독 후보를 만듭니다.
3. 각 Shift 값과 해독 결과를 화면에 출력합니다.
4. 해독 결과를 소문자로 바꾼 뒤 사전 키워드가 포함되어 있는지 확인합니다.
5. 사전 키워드가 발견되면 탐색을 중지합니다.
6. 발견된 해독 결과를 `result.txt`에 저장합니다.
7. 사전 키워드가 끝까지 발견되지 않으면 저장하지 않고 종료합니다.

## 핵심 로직

### 1. 모든 Shift 값으로 해독하기

```python
for shift in range(ALPHABET_COUNT):
    decoded_text = ""
```

`ALPHABET_COUNT`는 알파벳 개수인 `26`입니다. 카이사르 암호에서 가능한 Shift 값은 `0~25`뿐이므로, 모든 경우를 순서대로 검사합니다.

이 방식은 암호에 사용된 Shift 값을 몰라도 가능한 결과를 전부 확인할 수 있다는 장점이 있습니다.

### 2. 대문자와 소문자 유지하기

```python
if "A" <= char <= "Z":
    decoded_text += chr((ord(char) - ord("A") - shift) % ALPHABET_COUNT + ord("A"))
elif "a" <= char <= "z":
    decoded_text += chr((ord(char) - ord("a") - shift) % ALPHABET_COUNT + ord("a"))
else:
    decoded_text += char
```

문자를 해독할 때 대문자는 대문자로, 소문자는 소문자로 유지합니다.

알파벳이 아닌 공백, 숫자, 특수문자는 암호화 대상이 아니므로 그대로 남겨 둡니다. 이렇게 하면 원래 문장의 띄어쓰기와 문장 구조가 보존되어 해독 결과를 더 쉽게 읽을 수 있습니다.

### 3. 모듈러 연산으로 알파벳 순환 처리하기

```python
(ord(char) - ord("A") - shift) % ALPHABET_COUNT
```

알파벳을 뒤로 이동하다 보면 `A`보다 앞쪽으로 넘어가는 경우가 생깁니다. 예를 들어 `A`를 1칸 되돌리면 다시 `Z`가 되어야 합니다.

`% ALPHABET_COUNT`는 이런 순환 처리를 간단하게 해결합니다. 별도의 조건문으로 `A`보다 작아졌는지 검사하지 않아도, 계산 결과가 항상 `0~25` 범위 안에 머물게 됩니다.

### 4. 사전 키워드로 자동 탐색 중지하기

```python
DICTIONARY = ["mars", "base", "password", "system", "secret", "danger", "login"]
```

`DICTIONARY`는 해독 결과에서 찾을 단어 목록입니다. 암호문이 올바르게 해독되면 문장 안에 `mars`, `base`, `password` 같은 의미 있는 단어가 포함될 가능성이 높습니다.

```python
lower_decoded = decoded_text.lower()
for word in DICTIONARY:
    if word in lower_decoded:
        print(f"사전의 키워드 '{word}'(을)를 발견하여 탐색을 중지합니다. (shift: {shift})")
        return decoded_text
```

해독 결과를 `lower()`로 소문자로 바꾼 뒤 사전 단어와 비교합니다. 이렇게 하면 원문에 `Mars`, `MARS`, `mars`처럼 대소문자가 다르게 들어 있어도 같은 단어로 인식할 수 있습니다.

사전 단어가 발견되면 해당 Shift 값이 정답일 가능성이 높다고 판단하고, 더 이상 나머지 Shift 값을 검사하지 않습니다. 불필요한 반복을 줄이고 결과 저장까지 자동으로 이어지게 하는 부분입니다.

### 5. 안전한 파일 읽기와 쓰기

```python
try:
    with open("password.txt", "r", encoding="utf-8") as file:
        return file.read()
except FileNotFoundError:
    print("password.txt 파일을 찾을 수 없습니다.")
```

파일 입출력은 파일이 없거나 권한이 부족한 경우 실패할 수 있습니다. 그래서 `try-except`로 오류 상황을 처리합니다.

또한 `with open(...)`을 사용해 파일을 열면, 작업이 끝났을 때 파일이 자동으로 닫힙니다. 중간에 오류가 발생해도 파일 자원이 정리되므로 더 안전합니다.

## 예시

`password.txt` 내용이 아래와 같다면:

```text
B ehox Ftkl
```

프로그램은 가능한 해독 결과를 모두 출력합니다. 그중 의미가 맞는 결과는 다음과 같습니다.

```text
I love Mars
```

이 결과에는 사전 단어인 `mars`가 포함되어 있습니다. 프로그램은 대소문자를 구분하지 않고 키워드를 검사하므로 `Mars`도 `mars`와 같은 단어로 판단합니다.

따라서 해당 결과를 찾는 순간 반복을 멈추고, 최종 해독문을 `result.txt`에 저장합니다.

## 정리

이 프로그램은 카이사르 암호의 Shift 값을 모를 때 사용할 수 있는 간단한 해독 도구입니다. 핵심은 모든 Shift 값을 시도하는 브루트 포스 방식이며, 텍스트 사전을 활용해 의미 있는 단어가 발견되는 순간 자동으로 탐색을 멈추도록 구성되어 있습니다.
