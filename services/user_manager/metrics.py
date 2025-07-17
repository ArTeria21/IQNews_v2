from prometheus_client import CollectorRegistry, Counter, Histogram

user_manager_registry = CollectorRegistry()

USER_CREATED_COUNTER = Counter(
    "user_created_count",
    "Количество созданных пользователей",
    registry=user_manager_registry,
)

REQUEST_COUNTER = Counter(
    "request_count",
    "Количество запросов",
    registry=user_manager_registry,
    labelnames=["request_type"],
)

TIME_OF_OPERATION = Histogram(
    "time_of_operation",
    "Время выполнения запроса",
    registry=user_manager_registry,
    buckets=[0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 60],
    labelnames=["request_type"],
)

ERROR_COUNTER = Counter(
    "error_count",
    "Количество ошибок",
    registry=user_manager_registry,
    labelnames=["error_type"],
)
