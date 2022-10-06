import io, os
import hydra
from omegaconf import DictConfig
from typing import Any, List, MutableMapping

import wave
import csv
import librosa
import soundfile as sf
import subprocess
import pygame
from colorama import Fore, Back, Style
import requests
from bs4 import BeautifulSoup
import readline
import whisper
from pathlib import Path

class Worker:
    def __init__(self, settings: MutableMapping[str, Any], params: MutableMapping[str, Any]):
        # サンプリング周波数の設定
        self.fs = params['fs']
        # モノラルで読み込むか
        self.mono = params['mono']
        # 何bitで書き込むか
        self.subtype = params['subtype']

        # ルートディレクトリの設定
        self.root_dir = Path(settings['root_dir'])

        # 音声ファイル名
        self.source_name = settings['source_name']

        # wav変換前の音声ファイルパス
        self.before_converted_audio_path = self.root_dir.joinpath(settings['source_name'] + settings['file_format'])
        # wav変換後の音声ファイルパス
        self.converted_audio_path = self.root_dir.joinpath(settings['source_name'] + '/' + settings['source_name'] + '.wav')

        # 文字起こし結果を書き込むcsvファイルのパス
        self.result_csv_path = self.root_dir.joinpath(settings['source_name'] + '/' + settings['source_name'] + '_result.csv')

        # 暗記アプリにインポートするためのcsvファイルパス
        self.csv_path_for_wordholic = settings['csv_path']

        # 分割後音ファイルのディレクトリ
        self.splited_audio_path = self.root_dir.joinpath(settings['source_name'] + '/' + 'splited_audio')

        # whisperモデルの設定
        self.model = params['whisper']['type']
        self.verbose = params['whisper']['verbose']
        self.language = params['whisper']['language']

    def convert_to_wav(self) -> None:
        """
        音声ファイルをwav形式に変換する
        """

        # すでにwav形式の場合、retrun
        if '.wav' in str(self.before_converted_audio_path):
            print(Fore.LIGHTRED_EX + 'Audio file is already converted to .wav' + Style.RESET_ALL)
            return 

        else:
            # 音ファイルの読み込み
            y, sr = librosa.core.load(self.before_converted_audio_path, sr=self.fs, mono=self.mono)

            # wavに変換
            sf.write(self.converted_audio_path, y, sr, subtype=self.subtype)
            subprocess.run([f'rm {self.before_converted_audio_path}'],shell=True)
    

    def speech_to_text(self) -> None:
        """
        whisperを用いて音声データを文字起こしする
        """
        # 音ファイル全体の長さの表示
        print('original: {:.2f} [min]'.format(self.get_audio_length(str(self.converted_audio_path))/60))

        # whisper モデルをload
        model = whisper.load_model(self.model)
        # whisperを実行
        results = model.transcribe(str(self.converted_audio_path), verbose=self.verbose,language=self.language)

        # csv_fileに文字起こし結果を書き込む
        with open(self.result_csv_path, 'w') as f:
            header = ['id', 'start', 'end', 'Text']
            writer = csv.writer(f)
            if not os.path.isdir(self.result_csv_path):
                writer.writerow(header)
            
            for line in results["segments"]:
                writer.writerow([line['id'], line['start'], line['end'],line['text']])


    def interactive(self) -> None:
        """
        文字起こし結果を1文ずつ見ながらインタラクティブシェル上で学習
        """

        # 文字起こしデータの読み込み
        results = []
        with open(self.result_csv_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                results.append(row)
        
        # 一行ずつ表示する
        for idx, row in enumerate(results[1:]):
            print(f'file number : {idx + 1}/{len(results)} [current/all]')

            # 認識された文章の表示
            print(Style.RESET_ALL + Fore.LIGHTYELLOW_EX + str(row[3]) + Style.RESET_ALL)
            
            while True:
                # 入力の受付
                process = input(Fore.CYAN + "Press any keys : " + Style.RESET_ALL)

                # 音の再生
                if process == 'a':
                    # 該当区間の切り取り
                    sep_path = self.cut_audio(row)
                    self.play_audio(str(sep_path))
                    
                # 語彙の追加 
                elif process == 'v':
                    vocab = input('Vocabulary : ')
                    meaning = input('meaning : ')
                    comment = input('comment : ')
                    if vocab != '' and meaning != '':
                        self.write_csv(vocab, meaning, comment, mode = 'vocab')
                    else:
                        print(Fore.LIGHTRED_EX + 'Failed to append vocabulary' + Style.RESET_ALL)

                # 文章の追加
                elif process == 's':
                    phrase = input('Sentence : ')
                    meaning = input('meaning : ')
                    comment = input('comment : ')
                    if phrase != '' and meaning != '':
                        self.write_csv(phrase, meaning, comment, mode = 'sentence')
                    else:
                        print(Fore.LIGHTRED_EX + 'Failed to append sentence' + Style.RESET_ALL)

                # 発音の追加
                elif process == 'p':
                    vocab = input('word : ')
                    meaning = None
                    comment = input('comment : ')
                    if vocab != '':
                        self.write_csv(vocab, meaning, comment, mode = 'pronunciation')
                    else:
                        print(Fore.LIGHTRED_EX + 'Failed to append pronunciation' + Style.RESET_ALL)

                # 操作コマンドの一覧表示
                elif process == 'help': 
                    print('a: 音ファイルを再生します')
                    print('v: 語彙を追加します')
                    print('s: 文章を追加します')
                    print('p: 発音を追加します')
                    print('n: 次の文章に移行します')
                
                # 次の文章へ
                elif process == 'n':
                    break

                # 上記以外のキーが押されたとき、注意文を出力
                else:
                    print(Fore.LIGHTRED_EX + 'Press other keys. If you want to know commands, please push "help".' + Style.RESET_ALL)
        
        return

    def cut_audio(self, row: List) -> Path:
        # データから該当区間の開始時間、終了時間を取得
        id, start, end = row[0], float(row[1]), float(row[2])

        # 分割後の音ファイルを格納するディレクトリの作成
        subprocess.run([f'mkdir -p {self.splited_audio_path}'],shell=True)

        if not os.path.isfile(self.splited_audio_path.joinpath(self.source_name + "_" +f'{id}.wav')):
            # 分割後の音声ファイルパス
            splited_path = self.splited_audio_path.joinpath(self.source_name + "_" + id + ".wav")
            # 音声ファイルから該当区間を切り取る
            subprocess.run([f'ffmpeg -i {self.converted_audio_path} -loglevel quiet -ss {start} -t {end - start} {splited_path}'],shell=True)

        return splited_path

    def play_audio(self, audio_path: str, audio_length=None) -> None:
        # 再生する音声データの長さを取得
        if audio_length is None:
            audio_length = self.get_audio_length(audio_path)
        print(f'再生時間は {audio_length}[s]です')
        
        # pygameのsetting
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play(loops=0)

        while True:
            process = input("Audio is playing...")
            # 音の再生を止める
            if process == 'q':
                pygame.mixer.music.stop()
                break

            # 初めから再生する
            elif process == 'r':
                self.play_audio(audio_path)

            # 上記以外のキーが押されたとき、注意文を出力
            elif process != 'q' or process != 'r':
                print("Press 'q' or 'r'")
        print('Audio end')
        return
    
    # audioの長さを取得する
    def get_audio_length(self, audio_path: str) -> float:
        with wave.open(audio_path, 'rb') as wr:
            fr = wr.getframerate()
            fn = wr.getnframes()

        return (1.0 * fn / fr)

    def write_csv(self,front: str, back: str, comment: str, mode: str) -> None:
        # ファイルの有無
        file_exists = os.path.isfile(self.csv_path_for_wordholic + f'{self.source_name}_{mode}.csv')
        
        if mode == 'pronunciation':
            back = get_examples(front)
            if back == "":
                print(Fore.LIGHTRED_EX + 'Failed to getting symbol' + Style.RESET_ALL)
                return
            
        # 書き込み
        with open(self.csv_path_for_wordholic + f'{self.source_name}_{mode}.csv', 'a') as f:
            header = ['FrontText', 'BackText', 'Comment', 'FrontTextLanguage', 'BackTextLanguage']
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow([front, back, comment,'en-US', 'ja-JP'])
            
        print(f'Complete appending {mode} ')
        return

def get_examples(word: str) -> str:
    """
    スクレイピングをして発音記号を取得
    """

    # スクレイピングするサイト
    base_url = "http://eow.alc.co.jp/search"
    query = {}
    query["q"] = word
    query["ref"] = "sa"
    ret = requests.get(base_url,params=query)
    text = ""
    soup = BeautifulSoup(ret.content,"lxml")

    # 検索結果がないとき
    if soup.findAll("div",{"id":"resultsList"}) == []:
        return text

    for l in soup.findAll("div",{"id":"resultsList"})[0]:
        try:
            if '【発音】' in l.text:
                text = l.text.split('【発音】')[-1].split('【＠】')[0] + text.split('【発音】')[-1].split('【＠】')[-1].split('【')[0]
                break
            elif '【発音！】' in l.text:
                text = l.text.split('【発音！】')[-1].split('【＠】')[0] + text.split('【発音！】')[-1].split('【＠】')[-1].split('【')[0]
                break

        except:
            pass

    return text

@hydra.main(config_path='/Users/tsubaki/Desktop/DMM_recordings/convert_conversation_with_whisperAI', config_name = 'main_settings.yaml')
def main(cfg:DictConfig):

    # Load settings
    workflow = cfg.workflow
    settings = cfg.settings
    params = cfg.params

    # Worker クラスのインスタンス作成
    worker = Worker(settings, params)

    # wavに変換するか
    if workflow['convert_to_wav']:
        worker.convert_to_wav()

    # 文字起こしを行うか
    if workflow['speech_to_text']:
        worker.speech_to_text()

    # インタラクティブシェル上で学習を行うか
    if workflow['interactive']:
        worker.interactive()

if __name__ == "__main__":
    main()

    