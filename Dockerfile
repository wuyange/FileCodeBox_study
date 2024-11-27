FROM python:3.12.1
COPY . /app
WORKDIR /app
RUN pip install --no-index --find-links=packages -r requirements.txt
EXPOSE 80
CMD ["python","main.py"]