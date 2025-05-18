FROM tensorflow/tensorflow:latest-gpu

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN apt-get update && apt-get install -y libgl1

RUN pip install --upgrade pip

RUN pip install --no-cache-dir --upgrade --ignore-installed blinker -r /code/requirements.txt

COPY ./app /code/app

VOLUME ["/code/data/events_imgs"]
VOLUME ["/code/data/people_imgs"]

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
