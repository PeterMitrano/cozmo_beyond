from BlinkPipeline import Pipeline


class GripWrapper:

    def __init__(self):
        self.pipeline = Pipeline()

    def run(self, source):
        self.pipeline.set_source0(source)
        self.pipeline.process()
        return (self.pipeline.cv_adaptivethreshold_output, min(1, len(self.pipeline.find_blobs_output)))

