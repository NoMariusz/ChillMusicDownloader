:: script building cmdownloader app executable
:: !!! don't forget activate your venv before start
:: be aware that you must prepare in ./dev folder:
::  - base_config.json with default config.json file
::  - base_last_track.json with default last_track.json file
::  - google_api_python_client-1.9.3.dist-info folder with necessary files
:: to made executalbe work from this library

@echo off

echo Start work

:: define constant variables
set main_path=%cd%

:: set main_file_path=%main_path%\app\chill_music_downloader.py
set main_file_path=%main_path%\dev\Chill Music Downloader.spec
set ico_path=%main_path%\data\graphics\CMDownloader_logo.ico

set result_path=D:\files

:: make and go to temp folder
mkdir build
cd  build

@echo on

:: run pyinstaller
:: pyinstaller "%main_file_path%" -i "%ico_path%" -n "Chill Music Downloader" -c --specpath "%main_path%\dev"
pyinstaller "%main_file_path%" -i "%ico_path%" -n "Chill Music Downloader" -c

@echo off

:: copy dist
xcopy dist\"Chill Music Downloader"\ ^
    %result_path%\"Chill Music Downloader"\app\ /E/H/I/Y
:: copy additional files
xcopy %main_path%\data\ %result_path%\"Chill Music Downloader"\data\ /E/H/I
xcopy %main_path%\dev\base_config.json ^
    %result_path%\"Chill Music Downloader"\data\config.json /H/I/Y
xcopy %main_path%\dev\base_last_track.json ^
    %result_path%\"Chill Music Downloader"\data\last_track.json /H/I/Y
xcopy %main_path%\app\ffmpeg.exe ^
    %result_path%\"Chill Music Downloader"\app\ffmpeg.exe* /H/I
:: copy broken library (pyinstaller don't copy that)
set broken_library_name=google_api_python_client-1.9.3.dist-info
xcopy %main_path%\dev\%broken_library_name%\ ^
    %result_path%\"Chill Music Downloader"\app\%broken_library_name%\ /E/H/I

:: clear after work
cd ..
rmdir build /S/Q

echo End work
