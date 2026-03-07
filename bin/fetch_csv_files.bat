@echo off

REM ---- sprawdzenie argumentów ----

if "%~1"=="" (
    echo ERROR: Podaj katalog docelowy
    echo Uzycie: download_csv.bat DEST_DIR AWS_PROFILE
    exit /b 1
)

if "%~2"=="" (
    echo ERROR: Podaj profil AWS
    echo Uzycie: download_csv.bat DEST_DIR AWS_PROFILE
    exit /b 1
)

set DEST=%~1
set PROFILE=%~2

REM ---- blokada niebezpiecznych sciezek ----

if /I "%DEST%"=="." (
    echo ERROR: Niedozwolona sciezka "."
    exit /b 1
)

if /I "%DEST%"=="\" (
    echo ERROR: Niedozwolona sciezka "\"
    exit /b 1
)

if /I "%DEST%"=="C:\" (
    echo ERROR: Niedozwolona sciezka "C:\"
    exit /b 1
)

if /I "%DEST%"=="D:\" (
    echo ERROR: Niedozwolona sciezka "D:\"
    exit /b 1
)

REM ---- katalog musi istniec ----

if not exist "%DEST%" (
    echo ERROR: Katalog "%DEST%" nie istnieje
    exit /b 1
)

echo Cleaning "%DEST%"
rm -rf "%DEST%"/*.csv

echo Downloading CSV files...
echo on

aws s3 sync ^
    s3://sebcel-receipt-analyzer-processed-bucket-dev/exports/receipts ^
    "%DEST%" ^
    --exclude "*" ^
    --include "*.csv" ^
    --profile %PROFILE%

echo Done.