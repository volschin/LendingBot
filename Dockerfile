FROM python:3.7-slim
LABEL "project.home"="https://github.com/BitBotFactory/poloniexlendingbot"

#
# Build: docker build -t <your_id>/pololendingbot .
# Run: docker run -d -v /pololendingbot_data:/data -p 8000:8000 <your_id>/pololendingbot
#

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

COPY . .

VOLUME /data

RUN ln -s /data/market_data market_data; \
    ln -s /data/log/botlog.json www/botlog.json; \
    ln -s /data/history.json www/history.json; \
    ln -s /data/rates.json www/rates.json

EXPOSE 8000

HEALTHCHECK CMD curl --fail-early -ISs http://localhost:8000/ |grep P/ || exit 1
CMD ["python", "lendingbot.py", "-cfg", "default.cfg"]
