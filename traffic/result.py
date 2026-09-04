class TrafficResult:
    def __init__(self, raw_output, metadata=None, metrics=None):

        self.raw_output = raw_output

        self.metadata = metadata if metadata is not None else {}

        self.metrics = metrics if metrics is not None else {}
