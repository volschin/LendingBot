FROM amancevice/pandas:slim
#FROM python:3.9-slim
LABEL "project.home"="https://github.com/volschin/LendingBot"

#
# Build: docker build -t <your_id>/pololendingbot .
# Run: docker run -d -v /pololendingbot_data:/data -p 8000:8000 <your_id>/pololendingbot
#
ENV DEBIAN_FRONTEND noninteractive
ENV TERM xterm
# Install base environment
RUN apt-get update \
  && apt-get install -qqy --no-install-recommends apt-utils \
  apt-transport-https \
  curl \
  nano \
  sqlite3 \
  && apt-get autoremove -y && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

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
