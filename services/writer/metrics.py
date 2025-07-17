from prometheus_client import CollectorRegistry, Counter, Histogram

writer_registry = CollectorRegistry()

AMOUNT_OF_SUMMARIES = Counter(
    "amount_of_summaries",
    "Количество сгенерированных саммари",
    registry=writer_registry,
)

SUMMARY_LENGTH = Histogram(
    "summary_length",
    "Длина сгенерированного саммари",
    registry=writer_registry,
    buckets=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000],
)

ERROR_COUNTER = Counter(
    "error_count",
    "Количество ошибок",
    registry=writer_registry,
    labelnames=["error_type"],
)

TIME_OF_OPERATION = Histogram(
    "time_of_operation",
    "Время выполнения запроса",
    registry=writer_registry,
    buckets=[0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 60],
    labelnames=["request_type"],
)
