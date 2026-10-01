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

    def report_callback_error(exc):
        if on_error is None:
            return
        try:
            on_error(exc, traceback.format_exc())
        except Exception:
            # Never let an error-reporting callback prevent the finalizer from
            # restoring disabled buttons/state.
            pass

    def poll():
        finished = False
        while True:
            try:
                kind, value, details = messages.get_nowait()
            except queue.Empty:
                break

            if kind == "success" and on_success is not None:
                try:
                    on_success(value)
                except Exception as exc:
                    report_callback_error(exc)
            elif kind == "error" and on_error is not None:
                try:
                    on_error(value, details)
                except Exception:
                    pass
            elif kind == "finished":
                finished = True
                if on_finally is not None:
                    try:
                        on_finally()
                    except Exception:
                        pass

        if not finished and thread.is_alive():
            root.after(50, poll)
        elif not finished:
            # The worker can exit between the queue drain and is_alive().
            root.after(0, poll)

    thread.start()
    root.after(50, poll)
    return thread
