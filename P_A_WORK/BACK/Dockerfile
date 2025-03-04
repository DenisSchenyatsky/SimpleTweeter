FROM python:3.12-slim
WORKDIR /home
#COPY . /home/app
RUN mkdir /home/app
COPY ./requirements.txt /home/app
RUN  mkdir /home/DB
RUN pip install --upgrade pip
RUN pip install -r /home/app/requirements.txt


CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]