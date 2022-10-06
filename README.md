# convert_conversation_with_Whisper

## Overview
This is a tool for English learners using the [Whisper API](https://github.com/openai/whisper) released by OpenAI to transcribe English conversation audio. 
While checking the results of the transcription one sentence at a time, you can listen to the audio of the corresponding part, or add words, sentences, etc. to the csv file.
The created csv file will be created in a form suitable for [WordHolic](https://www.langholic.com/wordholic), allowing you to efficiently create memorization cards on the application.

OpenAIが公開している[Whisper API](https://github.com/openai/whisper)を利用して、英会話音声を書き起こす英語学習者向けツールです。
文字起こしの結果を1文ずつ確認しながら、該当箇所の音声を聴く、csvファイルに単語、文などを追加することができます。
作成したcsvファイルは[WordHolic](https://www.langholic.com/wordholic)に適した形で作成され、アプリ上で効率的に暗記カードを作成することができます。

## Before run
Append your settings to main_settings.yaml and convert_conversation.py

## Run
```
python convert_conversation.py
```

## Examples
●文字起こし結果を1文ずつ表示している画面　　
<img width="571" alt="スクリーンショット 2022-10-06 15 56 02" src="https://user-images.githubusercontent.com/85504048/194234742-b474af50-1523-433d-8d31-e6e625102ee3.png">

●文字起こし結果（I can hear you and I can see you very clearly as well.）の音声ファイルを再生している画面
<img width="418" alt="スクリーンショット 2022-10-06 15 42 29" src="https://user-images.githubusercontent.com/85504048/194232631-6d0c0fb6-cc1a-4dbc-8e5c-7465a3361413.png">

●文字起こし結果（I can hear you and I can see you very clearly as well.）から覚えたい表現をcsvファイルに画面
<img width="469" alt="スクリーンショット 2022-10-06 15 51 01" src="https://user-images.githubusercontent.com/85504048/194233768-d1265c8c-8cb7-46f5-af33-893454412243.png">

## LICENSE
MIT
