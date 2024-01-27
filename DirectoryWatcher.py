import time
import rarfile
from watchdog.observers import Observer

from Handler import Handler


class Watcher:
    def __init__(self, directory_to_watch, config):
        self.DIRECTORY_TO_WATCH = directory_to_watch
        self.config = config
        rarfile.UNRAR_TOOL = self.config['unrar_tool']
        self.observer = Observer()

    def run(self):
        event_handler = Handler(self.config)
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        print(f"Observer started. Monitoring {self.DIRECTORY_TO_WATCH}")
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()
