import ctypes
import pipewire_filtertools as pfts


class LoopCtx(ctypes.Structure):
    _fields_ = [
        ("buffer_ptr", ctypes.POINTER(ctypes.c_float)),
        ("buffer_size", ctypes.c_size_t),
        ("n_samples", ctypes.c_uint32),
        ("have_data", ctypes.c_int),
    ]


def main():
    rate = 48000
    quantum = 128
    pfts.init()
    rate = pfts.get_rate() or rate

    buf_size = quantum * 2
    ArrayType = ctypes.c_float * buf_size
    buffer = ArrayType()
    ctx = LoopCtx(buffer, buf_size, 0, 0)
    ctx_p = ctypes.pointer(ctx)

    ON_BUFFER = pfts.PIPEWIRE_FILTERTOOLS_ON_BUFFER
    memmove = ctypes.memmove
    fsize = ctypes.sizeof(ctypes.c_float)

    @ON_BUFFER
    def on_capture(c_ctx, samples, n_samples):
        lc = ctypes.cast(c_ctx, ctypes.POINTER(LoopCtx)).contents
        n = min(n_samples, lc.buffer_size)
        memmove(lc.buffer_ptr, samples, n * fsize)
        lc.n_samples = n
        lc.have_data = 1

    @ON_BUFFER
    def on_playback(c_ctx, samples, n_samples):
        lc = ctypes.cast(c_ctx, ctypes.POINTER(LoopCtx)).contents
        if lc.have_data:
            n = min(n_samples, lc.n_samples)
            memmove(samples, lc.buffer_ptr, n * fsize)
            lc.have_data = 0
        else:
            memmove(samples, (ctypes.c_char * (n_samples * fsize))(), n_samples * fsize)

    loop = pfts.main_loop_new()
    print(f"[pipewire-filtertools] Running loopback: rate={rate}, quantum={quantum}")
    pfts.main_loop_run(ctypes.cast(ctx_p, ctypes.c_void_p), loop, rate, quantum, on_capture, on_playback)
    pfts.deinit()
