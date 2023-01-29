FROM python:latest

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NOWARNINGS="yes"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR "/webscraper"

COPY . .
RUN ["chmod", "+x", "/webscraper/entrypoint.sh"]

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils; apt-get install -y cron

RUN pip install --no-cache-dir -r requirements.txt

RUN crontab crontab

ENTRYPOINT ["/webscraper/entrypoint.sh"]
