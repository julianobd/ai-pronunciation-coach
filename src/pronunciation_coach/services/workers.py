"""Background execution helpers: run any callable on the global QThreadPool."""

from __future__ import annotations

import traceback

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()


class FunctionWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        # The pool must NOT delete this runnable when run() returns: the
        # result/error signals are delivered to the main thread as queued
        # events, and deleting the signals object before they are processed
        # silently drops them (the UI would wait forever). Lifetime is
        # managed by _active_workers in run_in_background instead.
        self.setAutoDelete(False)

    def _emit(self, signal, *args) -> None:
        try:
            signal.emit(*args)
        except RuntimeError:
            pass  # app shut down while we were running; nobody is listening
        except Exception:
            traceback.print_exc()  # a directly-connected slot raised

    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            self._emit(self.signals.error, traceback.format_exc())
        else:
            self._emit(self.signals.result, result)
        finally:
            self._emit(self.signals.finished)


# Strong references to in-flight workers. Removed only after the worker's
# `finished` signal is processed on the main thread, which is guaranteed to
# happen after `result`/`error` (emitted earlier from the same thread).
_active_workers: set[FunctionWorker] = set()


def run_in_background(fn, *args, on_result=None, on_error=None,
                      on_finished=None, **kwargs) -> FunctionWorker:
    worker = FunctionWorker(fn, *args, **kwargs)
    if on_result:
        worker.signals.result.connect(on_result)
    if on_error:
        worker.signals.error.connect(on_error)
    if on_finished:
        worker.signals.finished.connect(on_finished)

    _active_workers.add(worker)
    worker.signals.finished.connect(lambda: _active_workers.discard(worker))

    QThreadPool.globalInstance().start(worker)
    return worker


def wait_for_workers(timeout_ms: int = 10000) -> None:
    QThreadPool.globalInstance().waitForDone(timeout_ms)
