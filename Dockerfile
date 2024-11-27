FROM centos7
COPY . /app
WORKDIR /app
COPY ./python-3.9.7.tar.gz /tmp/
RUN tar -xzf /tmp/python-3.9.7.tar.gz -C /tmp && \
    cd /tmp/Python-3.9.7 && \
    ./configure && make && make install
RUN pip install --no-index --find-links=packages -r requirements.txt
EXPOSE 80
CMD ["python","main.py"]