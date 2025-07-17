from prometheus_client import CollectorRegistry, Counter, Histogram

rss_manager_registry = CollectorRegistry()

AMOUNT_OF_POSTS = Counter(
    "amount_of_posts",
    "Количество постов",
    registry=rss_manager_registry,
)

AMOUNT_OF_ADDED_RSS_FEEDS = Counter(
    "amount_of_added_rss_feeds",
    "Количество добавленных RSS-каналов",
    registry=rss_manager_registry,
)

TIME_OF_OPERATION = Histogram(
    "time_of_operation",
    "Время выполнения запроса",
    registry=rss_manager_registry,
    buckets=[0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 60],
    labelnames=["request_type"],
)

ERROR_COUNTER = Counter(
    "error_count",
    "Количество ошибок",
    registry=rss_manager_registry,
    labelnames=["error_type"],
)
