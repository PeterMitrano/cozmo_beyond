from BlinkPipeline import Pipeline


class GripWrapper:

    def __init__(self):
        self.pipeline = Pipeline()

    def run(self, source):
        self.pipeline.set_source0(source)
        self.pipeline.process()
        return source

