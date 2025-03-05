FROM python:3.12-slim
WORKDIR /home
#COPY . /home/app
RUN mkdir /home/BACK
COPY ./requirements.txt /home/BACK
RUN  mkdir /home/DB
RUN pip install --upgrade pip
RUN pip install -r /home/BACK/requirements.txt


CMD ["fastapi", "run", "BACK/main.py", "--host", "0.0.0.0", "--port", "8000"]