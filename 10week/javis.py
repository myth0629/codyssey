from __future__ import annotations

import argparse
import ctypes
import glob
from ctypes import wintypes
import os
import sys
import wave
from datetime import datetime

if os.name != 'nt':
    raise OSError('This recorder currently supports Windows only.')

WAVE_MAPPER = 0xFFFF_FFFF
WAVE_FORMAT_PCM = 1
WHDR_DONE = 0x0000_0001
WHDR_PREPARED = 0x0000_0002
WHDR_BEGINLOOP = 0x0000_0004
WHDR_ENDLOOP = 0x0000_0008
WHDR_INQUEUE = 0x0000_0010

MMSYSERR_NOERROR = 0
MMSYSERR_ALLOCATED = 4
MMSYSERR_BADDEVICEID = 2
MMSYSERR_NOTENABLED = 3
MMSYSERR_NOMEM = 7

WAVE_MAPPER_INDEX = ctypes.c_uint(-1).value
DWORD_PTR = getattr(wintypes, 'DWORD_PTR', ctypes.c_size_t)
# 녹음 파일은 정렬과 조회가 쉽도록 간단한 시간 형식으로 저장한다.
DATE_INPUT_FORMAT = '%Y-%m-%d'
RECORDING_TIMESTAMP_FORMAT = '%Y%m%d-%H%M%S'


def _check_mmresult(result: int, action: str) -> None:
    if result == MMSYSERR_NOERROR:
        return

    messages = {
        MMSYSERR_ALLOCATED: 'The audio device is already in use.',
        MMSYSERR_BADDEVICEID: 'The selected audio device is not available.',
        MMSYSERR_NOTENABLED: 'The audio device is disabled or unavailable.',
        MMSYSERR_NOMEM: 'The system ran out of memory while opening the device.',
    }
    detail = messages.get(result, f'Windows multimedia error code {result}.')
    raise RuntimeError(f'{action} failed: {detail}')


class WAVEFORMATEX(ctypes.Structure):
    _fields_ = [
        ('wFormatTag', wintypes.WORD),
        ('nChannels', wintypes.WORD),
        ('nSamplesPerSec', wintypes.DWORD),
        ('nAvgBytesPerSec', wintypes.DWORD),
        ('nBlockAlign', wintypes.WORD),
        ('wBitsPerSample', wintypes.WORD),
        ('cbSize', wintypes.WORD),
    ]


class WAVEHDR(ctypes.Structure):
    _fields_ = [
        ('lpData', wintypes.LPSTR),
        ('dwBufferLength', wintypes.DWORD),
        ('dwBytesRecorded', wintypes.DWORD),
        ('dwUser', DWORD_PTR),
        ('dwFlags', wintypes.DWORD),
        ('dwLoops', wintypes.DWORD),
        ('lpNext', wintypes.LPVOID),
        ('reserved', DWORD_PTR),
    ]


class WAVEINCAPSW(ctypes.Structure):
    _fields_ = [
        ('wMid', wintypes.WORD),
        ('wPid', wintypes.WORD),
        ('vDriverVersion', wintypes.DWORD),
        ('szPname', wintypes.WCHAR * 32),
        ('dwFormats', wintypes.DWORD),
        ('wChannels', wintypes.WORD),
        ('wReserved1', wintypes.WORD),
    ]


winmm = ctypes.windll.winmm
kernel32 = ctypes.windll.kernel32

waveInGetNumDevs = winmm.waveInGetNumDevs
waveInGetNumDevs.restype = wintypes.UINT

waveInGetDevCapsW = winmm.waveInGetDevCapsW
waveInGetDevCapsW.argtypes = [wintypes.UINT, ctypes.POINTER(WAVEINCAPSW), wintypes.UINT]
waveInGetDevCapsW.restype = wintypes.UINT

waveInOpen = winmm.waveInOpen
waveInOpen.argtypes = [
    ctypes.POINTER(wintypes.HANDLE),
    wintypes.UINT,
    ctypes.POINTER(WAVEFORMATEX),
    DWORD_PTR,
    DWORD_PTR,
    wintypes.DWORD,
]
waveInOpen.restype = wintypes.UINT

waveInPrepareHeader = winmm.waveInPrepareHeader
waveInPrepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(WAVEHDR), wintypes.UINT]
waveInPrepareHeader.restype = wintypes.UINT

waveInUnprepareHeader = winmm.waveInUnprepareHeader
waveInUnprepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(WAVEHDR), wintypes.UINT]
waveInUnprepareHeader.restype = wintypes.UINT

waveInAddBuffer = winmm.waveInAddBuffer
waveInAddBuffer.argtypes = [wintypes.HANDLE, ctypes.POINTER(WAVEHDR), wintypes.UINT]
waveInAddBuffer.restype = wintypes.UINT

waveInStart = winmm.waveInStart
waveInStart.argtypes = [wintypes.HANDLE]
waveInStart.restype = wintypes.UINT

waveInStop = winmm.waveInStop
waveInStop.argtypes = [wintypes.HANDLE]
waveInStop.restype = wintypes.UINT

waveInReset = winmm.waveInReset
waveInReset.argtypes = [wintypes.HANDLE]
waveInReset.restype = wintypes.UINT

waveInClose = winmm.waveInClose
waveInClose.argtypes = [wintypes.HANDLE]
waveInClose.restype = wintypes.UINT

waveInGetErrorTextW = winmm.waveInGetErrorTextW
waveInGetErrorTextW.argtypes = [wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
waveInGetErrorTextW.restype = wintypes.UINT


def list_input_devices() -> list[str]:
    device_count = waveInGetNumDevs()
    devices: list[str] = []

    for device_index in range(device_count):
        caps = WAVEINCAPSW()
        result = waveInGetDevCapsW(device_index, ctypes.byref(caps), ctypes.sizeof(caps))
        if result == MMSYSERR_NOERROR:
            devices.append(caps.szPname)

    return devices


def get_records_directory() -> str:
    base_directory = os.path.dirname(os.path.abspath(__file__))
    records_directory = os.path.join(base_directory, 'records')
    os.makedirs(records_directory, exist_ok=True)
    return records_directory


def build_recording_path(directory: str) -> str:
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    return os.path.join(directory, f'{timestamp}.wav')


def parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, DATE_INPUT_FORMAT)
    except ValueError as error:
        raise ValueError(f'Invalid date format: {value}. Use YYYY-MM-DD.') from error


def parse_recording_timestamp(file_path: str) -> datetime | None:
    file_name = os.path.basename(file_path)
    stem, extension = os.path.splitext(file_name)

    if extension.lower() != '.wav':
        return None

    # 시간 형식 이름 규칙을 따르지 않는 파일은 건너뛴다.
    try:
        return datetime.strptime(stem, RECORDING_TIMESTAMP_FORMAT)
    except ValueError:
        return None


def list_recordings_in_range(start_date: datetime, end_date: datetime) -> list[str]:
    records_directory = get_records_directory()
    matched_recordings: list[str] = []

    if end_date < start_date:
        raise ValueError('end_date must be greater than or equal to start_date.')

    # records 폴더의 WAV 파일만 읽어서 범위에 맞는 항목만 남긴다.
    for file_path in sorted(glob.glob(os.path.join(records_directory, '*.wav'))):
        recording_time = parse_recording_timestamp(file_path)
        if recording_time is None:
            continue

        if start_date <= recording_time <= end_date:
            matched_recordings.append(file_path)

    return matched_recordings


def resolve_listing_window(arguments: argparse.Namespace) -> tuple[datetime, datetime] | None:
    # 날짜 조건이 하나라도 있으면 새 녹음이 아니라 조회로 처리한다.
    should_list_recordings = arguments.list_recordings
    should_list_recordings = should_list_recordings or arguments.start_date is not None
    should_list_recordings = should_list_recordings or arguments.end_date is not None

    if not should_list_recordings:
        return None

    start_date = parse_date(arguments.start_date) if arguments.start_date is not None else datetime.min
    end_date = (
        parse_date(arguments.end_date).replace(hour=23, minute=59, second=59, microsecond=999999)
        if arguments.end_date is not None
        else datetime.max
    )
    return start_date, end_date


def create_wave_format(sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> WAVEFORMATEX:
    block_align = channels * (bits_per_sample // 8)
    avg_bytes_per_second = sample_rate * block_align
    return WAVEFORMATEX(
        wFormatTag=WAVE_FORMAT_PCM,
        nChannels=channels,
        nSamplesPerSec=sample_rate,
        nAvgBytesPerSec=avg_bytes_per_second,
        nBlockAlign=block_align,
        wBitsPerSample=bits_per_sample,
        cbSize=0,
    )


def record_audio(duration_seconds: float, output_path: str | None = None) -> str:
    if duration_seconds <= 0:
        raise ValueError('duration_seconds must be greater than 0.')

    records_directory = get_records_directory()
    if output_path is None:
        output_path = build_recording_path(records_directory)
    else:
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    sample_rate = 16000
    channels = 1
    bits_per_sample = 16
    buffer_seconds = max(duration_seconds, 1.0)
    buffer_size = int(sample_rate * channels * (bits_per_sample // 8) * buffer_seconds)

    wave_format = create_wave_format(sample_rate, channels, bits_per_sample)
    device_handle = wintypes.HANDLE()

    open_result = waveInOpen(
        ctypes.byref(device_handle),
        WAVE_MAPPER_INDEX,
        ctypes.byref(wave_format),
        0,
        0,
        0,
    )
    _check_mmresult(open_result, 'waveInOpen')

    buffer = ctypes.create_string_buffer(buffer_size)
    header = WAVEHDR()
    header.lpData = ctypes.cast(buffer, wintypes.LPSTR)
    header.dwBufferLength = buffer_size
    header.dwBytesRecorded = 0
    header.dwUser = 0
    header.dwFlags = 0
    header.dwLoops = 0
    header.lpNext = None
    header.reserved = 0

    try:
        _check_mmresult(
            waveInPrepareHeader(device_handle, ctypes.byref(header), ctypes.sizeof(header)),
            'waveInPrepareHeader',
        )
        _check_mmresult(
            waveInAddBuffer(device_handle, ctypes.byref(header), ctypes.sizeof(header)),
            'waveInAddBuffer',
        )
        _check_mmresult(waveInStart(device_handle), 'waveInStart')

        kernel32.Sleep(int(duration_seconds * 1000))

        _check_mmresult(waveInStop(device_handle), 'waveInStop')
        _check_mmresult(waveInReset(device_handle), 'waveInReset')

        recorded_size = int(header.dwBytesRecorded)
        if recorded_size <= 0:
            raise RuntimeError('No audio data was captured from the microphone.')

        with wave.open(output_path, 'wb') as audio_file:
            audio_file.setnchannels(channels)
            audio_file.setsampwidth(bits_per_sample // 8)
            audio_file.setframerate(sample_rate)
            audio_file.writeframes(buffer.raw[:recorded_size])
    finally:
        waveInUnprepareHeader(device_handle, ctypes.byref(header), ctypes.sizeof(header))
        waveInClose(device_handle)

    return output_path


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Record audio from the system microphone.')
    parser.add_argument(
        '--list-recordings',
        action='store_true',
        help='Show recordings saved in the date range and exit.',
    )
    parser.add_argument(
        '--start-date',
        default=None,
        help='Start date for listing recordings. Use YYYY-MM-DD.',
    )
    parser.add_argument(
        '--end-date',
        default=None,
        help='End date for listing recordings. Use YYYY-MM-DD.',
    )
    parser.add_argument(
        '-d',
        '--duration',
        type=float,
        default=5.0,
        help='Recording length in seconds.',
    )
    parser.add_argument(
        '-o',
        '--output',
        default=None,
        help='Optional output file path. Defaults to the records folder.',
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='Print available input device names and exit.',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)

    listing_window = resolve_listing_window(arguments)
    if listing_window is not None:
        start_date, end_date = listing_window
        recordings = list_recordings_in_range(start_date, end_date)

        if not recordings:
            print('No recordings found in the given date range.')
            return 0

        for recording_path in recordings:
            print(recording_path)
        return 0

    if arguments.list_devices:
        devices = list_input_devices()
        for index, device_name in enumerate(devices, start=1):
            print(f'{index}. {device_name}')
        return 0

    saved_path = record_audio(arguments.duration, arguments.output)
    print(saved_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
