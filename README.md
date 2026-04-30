# Thai หมิ่นประมาท Chatbot
This chatbot is a part of CP465 Text Mining 

# Setup
Download data from my [GoogleDrive](https://drive.google.com/drive/folders/1ZZIdGLfIbw2hEILRN9P7pEAgRN-ZT1vg?usp=sharing) and put it in your working directory

## Create Visual Enviroment
```bash
python -m venv env
```

## Install Requirement
```bash
pip install -r requirements.txt
```

## Inference
To run on CLI mode
```bash
python bot_app.py --mode cli
```

To run on [Telegram](https://telegram.org/) chatbot mode you need to create bot from [BotFather](https://telegram.me/BotFather) in [Telegram](https://telegram.org/) first
```bash
python bot_app.py --mode telelgram --token [BOT_TOKEN]
```

