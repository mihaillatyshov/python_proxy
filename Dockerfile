FROM python:3.11 AS build

COPY . /project
WORKDIR /project

RUN apt-get -y update && apt-get install -y postgresql
RUN pip3 install -r requirements.txt

USER postgres

RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER docker WITH SUPERUSER PASSWORD 'docker';" &&\
    createdb -O docker python_proxy &&\
    /etc/init.d/postgresql stop


USER root

EXPOSE 8000
EXPOSE 8080
ENV PGPASSWORD docker

CMD service postgresql start && \
    psql -h localhost -d python_proxy -U docker -p 5432 -a -q && \
    python3 main.py