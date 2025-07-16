@echo off
setlocal enabledelayedexpansion

set "VIDEO_PATH=video.mp4"
set "TOTAL_STREAMS=35"
set "LOG_DIR=logs"

if not exist "%VIDEO_PATH%" (
    echo ❌ File video.mp4 không tồn tại!
    pause
    exit /b
)

if not exist %LOG_DIR% mkdir %LOG_DIR%

echo Đang phát %TOTAL_STREAMS% luồng RTSP từ %VIDEO_PATH%...

for /L %%i in (1,1,%TOTAL_STREAMS%) do (
    set "CAM_ID=cam%%i"
    set "RTSP_URL=rtsp://localhost:8554/!CAM_ID!"

    start "" cmd /c ^
        ffmpeg -rtsp_transport tcp -re -stream_loop -1 -i "%VIDEO_PATH%" ^
        -vf "fps=7,scale=1280:720" -c:v libx264 -f rtsp !RTSP_URL! ^
        1> %LOG_DIR%\!CAM_ID!_stdout.log 2> %LOG_DIR%\!CAM_ID!_stderr.log
)

echo ✅ Đã gửi yêu cầu phát tới tất cả camera. Kiểm tra logs nếu cần.
pause
