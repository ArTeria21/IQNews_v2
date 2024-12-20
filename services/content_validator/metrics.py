from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

content_validator_registry = CollectorRegistry()

AMOUNT_OF_VALIDATED_POSTS = Counter('amount_of_validated_posts', 
                            'Количество проверенных постов',
                            registry=content_validator_registry)

TIME_OF_OPERATION = Histogram('time_of_operation', 
                            'Время выполнения запроса',
                            registry=content_validator_registry,
                            buckets=[0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 60],
                            labelnames=['request_type'])

MEAN_RATING = Gauge('mean_rating', 
                    'Средний рейтинг',
                    registry=content_validator_registry)

ERROR_COUNTER = Counter('error_count', 
                            'Количество ошибок',
                            registry=content_validator_registry,
                            labelnames=['error_type'])
