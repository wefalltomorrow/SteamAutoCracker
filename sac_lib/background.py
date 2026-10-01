import threading
import traceback


def run_background(root, worker, on_success=None, on_error=None, on_finally=None):
    """Run worker() off the Tk thread and marshal callbacks through root.after()."""
    def target():
        try:
            result = worker()
        except Exception as exc:
            details = traceback.format_exc()
            if on_error is not None:
                root.after(0, lambda: on_error(exc, details))
        else:
            if on_success is not None:
                root.after(0, lambda: on_success(result))
        finally:
            if on_finally is not None:
                root.after(0, on_finally)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread
