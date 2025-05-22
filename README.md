# Visit manager

## Development

## Basic functionality description
- endpoint: register, ponieważ o co chodzi z rejestracją -> człowiek klika żeby się zalogować przez google i za pierwszym razem jak się loguje musi jeszcze podać dane typu czy user, czy wendor itp use case opisany w 2.1.1, technicznie to podczas rejestracji on już musi mieć jwt googlowe, widziałem że ten ziomek z telekomony coś próbował na branchu OAuth ale to raczej do pomocy przy implementacji, no i generalnie w momencie rejestracji trzeba wysłać na kafke message już wybierz topic jaki chcesz że człowiek się zarejestrował, żeby móc to użyć w innych mikroserwisach,
- endpoint: register_visit --> zarejestrowanie wizyty: użytkownik chce móc zarejestrować wizytę u jakiegoś vendora (kiedy i jakie okresy czasu to to już będzie załatwione po stronie visit schedulera który wyśle na kafce że dana wizyta ma być dodana, request przyjdzie od visit_schedulera),
- endpoint: /vendor/my_visits --> dla wendora zwraca jakie on ma wizyty do odbycia,,
- endpoint: client/my_visits -->  dla usera jakie ma zaplanowane,
- endpoint: get_visit_code --> wendor powinien wypordukować kod dla danej wizyty który potem user potwierdzi,
- endpoint: check_visit_code --> user wpisuje kod który dostał od wendora i dostaje informację o jego poprawności --> na razie wizyt code to może być np. hash na bazie visit_id czy coś takiego w miarę prostego
- endpoint: add_opinion --> który powinien działać dopiero po końcu wizyty: dodanie rekomendacji w skali od 1-5, dodanie jej do bazy, oraz wysłanie na kafkę wiadomości z vendor_id i jego aktualną średnią


### Dependencies

The project manager used is [Poetry](https://python-poetry.org/) (version `>=2.0.0`).
It has to be installed and used in order to correctly add dependencies to the project.

Python `^3.11` is required. Install using [`pyenv`](https://github.com/pyenv/pyenv) (don't forget about [build dependencies](https://github.com/pyenv/pyenv)!):

```shell
pyenv install 3.11
```

Install the project in a local virtual environment:
```shell
PYENV_VERSION=3.11 python3 -m venv .venv
VIRTUAL_ENV=.venv poetry install --with dev
```

### Build

```shell
# production environment
docker build -t visit-manager:latest --target=prod .

# development environemnt (includes pytest, ruff, mypy and hot-reload)
docker build -t visit-manager:dev --target=dev .
```

### Development

# Dev variables defined in .env in dev-ops repo

- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_HOST
- POSTGRES_PORT
- KAFKA_BOOTSTRAP_URL
- KAFKA_GROUP_ID
- KAFKA_TOPIC
- KAFKA_AUTHENTICATION_SCHEME
- VISIT_MANAGER_LOG_LEVEL

#### Running the app

Run locally:

```shell
poetry run uvicorn --reload visit_manager.app.main:app --port 8080
 ```

Run the dev image with hot reload:

```shell
docker run -it --env-file=.env \
    --mount type=bind,src=$(pwd)/visit_manager,dst=/app/visit_manager \
    visit-manager:dev
```

Run the prod image:

```shell
docker run -it --env-file=.env visit-manager:latest
```

#### Contributing

```shell
poetry run pre-commit install
```

or run checks manually:

```shell
# verify pyproject.toml integrity
poetry check
# run tests
poetry run pytest
# run ruff check
poetry run ruff check [--fix]
# run mypy
poetry run mypy .
# reformat code
poetry run ruff format
```
