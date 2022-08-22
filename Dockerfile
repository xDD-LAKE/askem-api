FROM uwxdd/xdd-utilities:latest
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY src/ /app/src
COPY wsgi.py /app/
CMD ["gunicorn", "-b", "0.0.0.0:5000", "wsgi:app"]
