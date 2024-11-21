# IQNews
Команды для запуска Docker-контейнеров на время разработки:

- PostgreSQL:
    ```bash
    docker run -d \
    --name postgres-db \
    -e POSTGRES_USER=admin \
    -e POSTGRES_PASSWORD=admin \
    -e POSTGRES_DB=IQNews \
    -p 5432:5432 \
    postgres:latest
    ```

- RabbitMQ:
    ```bash
    docker run -d \
    --name rabbitmq-broker \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=admin \
    -p 5672:5672 \
    -p 15672:15672 \
    rabbitmq:3-management
    ```