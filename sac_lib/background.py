import queue
import threading
import traceback


def run_background(root, worker, on_success=None, on_error=None, on_finally=None):
    """Run worker() off the Tk thread and execute callbacks on the Tk thread."""
    messages = queue.Queue()

    def target():
        try:
            result = worker()
        except Exception as exc:
            messages.put(("error", exc, traceback.format_exc()))
        else:
            messages.put(("success", result, None))
        finally:
            messages.put(("finished", None, None))

    thread = threading.Thread(target=target, daemon=True)

    def poll():
        finished = False
        while True:
            try:
                kind, value, details = messages.get_nowait()
            except queue.Empty:
                break

            if kind == "success" and on_success is not None:
                on_success(value)
            elif kind == "error" and on_error is not None:
                on_error(value, details)
            elif kind == "finished":
                finished = True
                if on_finally is not None:
                    on_finally()

        if not finished and thread.is_alive():
            root.after(50, poll)

    thread.start()
    root.after(50, poll)
    return thread
