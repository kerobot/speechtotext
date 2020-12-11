from __future__ import division

import os
import re
import sys

from google.cloud import speech

import pyaudio
from six.moves import queue

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        # 音声レート
        self._rate = rate
        # フレームバッファサイズ
        self._chunk = chunk
        # 音声データを保持するためのスレッドセーフなキューを作成
        self._buff = queue.Queue()
        # 終了状態とする
        self.closed = True

    def __enter__(self):
        # 音声インターフェースを開始
        self._audio_interface = pyaudio.PyAudio()
        # 音声ストリームを開始
        self._audio_stream = self._audio_interface.open(
            # 16bit
            format=pyaudio.paInt16,
            # 1チャンネルのみサポート
            channels=1,
            # 音声レート(16000Hz)
            rate=self._rate,
            # 音声入力を対象とする
            input=True,
            # フレームバッファサイズ（1回に得るサイズ：16000Hz/10であれば100ms分）
            frames_per_buffer=self._chunk,
            # 音声ストリームから音声データを得るためのコールバックメソッドを指定
            stream_callback=self._fill_buffer,
        )
        # 開始状態とする
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        # 音声ストリームを停止
        self._audio_stream.stop_stream()
        # 音声ストリームを閉じる
        self._audio_stream.close()
        # 終了状態とすることで、generatorを終了させる
        self.closed = True
        # キューにNoneを追加することで、generatorを終了させる
        self._buff.put(None)
        # 音声インターフェースを終了
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        # コールバックメソッドとして、音声ストリームからキューに対して音声データを追加
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # キューから音声データが取得できるまでブロック
            chunk = self._buff.get()
            # キューから取得した音声データがNoneの場合はgenerator終了
            if chunk is None:
                return
            # ブロックして取得した音声データを保持
            data = [chunk]
            # キューに溜まっている残りの音声データもすべて取得
            while True:
                try:
                    # キューから音声データをブロックせずに取得（取得できなければ例外送出）
                    chunk = self._buff.get(block=False)
                    # キューから取得した音声データがNoneの場合はgenerator終了
                    if chunk is None:
                        return
                    # 取得した音声データを追加
                    data.append(chunk)
                except queue.Empty:
                    # キューが空の場合はキューからの音声データの取得を終了
                    break
            # キューから取得した音声データを結合したものをyield返却
            yield b"".join(data)

def listen_print_loop(responses):
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue
        # 音声認識の連続した結果を取得
        result = response.results[0]
        if not result.alternatives:
            continue
        # 結果のひとつから変換文字列を取得
        transcript = result.alternatives[0].transcript
        # 前回の印字文字数-変換文字数から、上書きする空白文字列を作成
        overwrite_chars = " " * (num_chars_printed - len(transcript))
        if not result.is_final:
            # 発話中は変換文字列+上書きする空白文字列を印字＋フラッシュ
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            # 今回の印字文字数を更新
            num_chars_printed = len(transcript)
        else:
            # 発話終了時は変換文字列+上書きする空白文字列を印字＋改行
            print(transcript + overwrite_chars)
            # 変換文字列が以下の場合は処理を終了する
            if re.search(r"\b(終了|終わり|おわり)\b", transcript, re.I):
                print("音声認識：終了中...")
                break
            # 今回の印字文字数をリセット
            num_chars_printed = 0

def main():
    # 環境変数：GOOGLE_APPLICATION_CREDENTIALSに、JSONファイルパスを設定しておくこと
    print("音声認識：開始中...")

    # 言語コード http://g.co/cloud/speech/docs/languages
    language_code = "ja-JP"
    # 音声検索やコマンドに適したモデル
    model = 'command_and_search'
    # 性能向上オプション（command_and_search で利用可能）
    use_enhanced = True
    # 音声適応による特定単語の候補指定
    speech_context = speech.SpeechContext(phrases=["精度","二重"])
    # 句読点の有効
    enable_automatic_punctuation = True
    # Google の Speech to text クライアント
    client = speech.SpeechClient()
    # Google の Speech to text の設定
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
        model=model,
        use_enhanced=use_enhanced,
        speech_contexts=[speech_context],
        enable_automatic_punctuation=enable_automatic_punctuation,
    )
    # Google の Speech to text の設定を指定し、発話途中の認識結果を有効化
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    print("音声認識：開始")

    # 音声レートとフレームバッファサイズを指定してストリームを開始
    with MicrophoneStream(RATE, CHUNK) as stream:
        # generatorメソッドを得る
        audio_generator = stream.generator()
        # generatorメソッドがyield返却した音声データを音声認識するジェネレーター式から
        # ジェネレーターオブジェクトを作成（入力オブジェクト）
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )
        # 設定と入力オブジェクトを指定して音声認識を実行
        responses = client.streaming_recognize(streaming_config, requests) #pylint: disable=too-many-function-args
        # 音声認識の結果を表示
        listen_print_loop(responses)

    print("音声認識：終了")

if __name__ == "__main__":
    main()
