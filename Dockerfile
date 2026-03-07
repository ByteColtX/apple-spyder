FROM python:3.14-alpine

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

EXPOSE 5005

CMD ["uv", "run", "python", "-m", "apple_spyder"]
