FROM python:3.10-slim as builder

ADD poetry.lock pyproject.toml ./

RUN pip install --no-build-isolation poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi



FROM python:3.10-slim

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

WORKDIR /app

ADD src .

ENTRYPOINT ["python", "main.py"]
