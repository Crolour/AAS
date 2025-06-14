# 📁 AAS — Automated Absenteeism System 

Автоматизированная система выставления прогулов студентам на сайт  колледжа

## 🧾 Описание 

Этот скрипт предназначен для автоматизации процесса выставления прогулов студентам в учебной системе.
Работает через Selenium и поддерживает: 

    • Авторизацию
    • Выбор даты (месяц/день)
    • Выбор студентов по номерам
    • Выбор причины прогула
    • Автоматическое проставление прогулов во все доступные ячейки
     

    ⚠️ Важно:  Используйте только с разрешения и в образовательных целях. 
     

## ✅ Функционал 

    • Вход в систему через логин/пароль
    • Сохранение данных между запусками (config.json)
    • Поддержка нескольких студентов
    • Выбор причины прогула: нет / мед.справка / объяснительная / общественная деятельность
    • Простановка прогулов во все доступные ячейки
    • Работа с куками для повторного входа
     

## 🛠 Требования 

    Python 3.8+
    Библиотеки: selenium, asyncio
    Драйвер браузера: chromedriver.exe или geckodriver.exe
    Браузер: Google Chrome (по умолчанию)

## Установите зависимости:
```
pip install selenium asyncio
```
