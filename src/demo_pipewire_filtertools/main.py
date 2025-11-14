import ctypes
import time
import os
import pipewire_filtertools as pfts


def main():
    rate = 48000
    quantum = 128
    pfts.init()
    rate = pfts.get_rate() or rate

    memmove = ctypes.memmove
    fsize = ctypes.sizeof(ctypes.c_float)

    last_call_time = ctypes.c_double(0.0)

    @pfts.PIPEWIRE_FILTERTOOLS_ON_PROCESS
    def on_process(_, in_samples, out_samples, n_samples):
        nonlocal last_call_time
        now = time.perf_counter()
        if last_call_time.value > 0:
            dt = now - last_call_time.value
            print(f"samples={n_samples}, Δt={dt*1000:.3f} ms")
        else:
            print(f"samples={n_samples}, first call")

        last_call_time.value = now
        memmove(out_samples, in_samples, n_samples * fsize)

    loop = pfts.main_loop_new()
    print(f"[pipewire-filtertools] Running loopback: rate={rate}, quantum={quantum}")
    pfts.main_loop_run(ctypes.c_void_p(), loop, f"demo-pipewire-filtertools-{os.getpid()}".encode(), True, rate, quantum, on_process)
    pfts.main_loop_destroy(loop)
    pfts.deinit()
