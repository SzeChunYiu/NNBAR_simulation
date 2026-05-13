"""
GPU Backend for NNBAR Reconstruction.

Provides a unified interface for NumPy/CuPy operations with automatic
GPU detection and fallback to CPU.

Usage:
    from nnbar_reconstruction.utils.gpu_backend import GPUBackend, get_backend

    gpu = get_backend()

    # Create arrays (automatically on GPU if available)
    x = gpu.array([1, 2, 3])

    # Use NumPy-like operations
    y = gpu.sqrt(x**2 + 1)

    # Transfer to CPU for sklearn/other libraries
    x_cpu = gpu.to_numpy(x)
"""

import os
import sys
import warnings
from typing import Any, Optional, Union, Tuple
import numpy as np

# Global state
_backend_instance: Optional['GPUBackend'] = None
_force_cpu: bool = False


def set_force_cpu(force: bool = True):
    """Force CPU-only mode (useful for debugging or when GPU is busy)."""
    global _force_cpu
    _force_cpu = force


class GPUBackend:
    """
    Unified backend for NumPy/CuPy operations.

    Automatically detects GPU availability and provides a consistent
    interface for array operations.
    """

    def __init__(self, device_id: int = 0, memory_pool_fraction: float = 0.8):
        """
        Initialize GPU backend.

        Args:
            device_id: CUDA device ID to use.
            memory_pool_fraction: Fraction of GPU memory to allocate for pool.
        """
        self.device_id = device_id
        self._use_gpu = False
        self._cupy = None
        self._cuml_available = False
        self._cudf_available = False

        if _force_cpu:
            self._init_cpu_only()
            return

        try:
            import cupy as cp

            # Test GPU availability
            cp.cuda.Device(device_id).use()

            # Allocate a small array to verify GPU works
            test = cp.array([1, 2, 3])
            _ = cp.asnumpy(test)

            self._cupy = cp
            self._use_gpu = True

            # Configure memory pool
            mempool = cp.get_default_memory_pool()
            mempool.set_limit(fraction=memory_pool_fraction)

            # Check for cuML
            try:
                import cuml
                self._cuml_available = True
            except ImportError:
                pass

            # Check for cuDF
            try:
                import cudf
                self._cudf_available = True
            except ImportError:
                pass

            # Get GPU info
            device = cp.cuda.Device(device_id)
            mem = device.mem_info
            total_gb = mem[1] / (1024**3)
            free_gb = mem[0] / (1024**3)

            print(f"[GPU Backend] Initialized on GPU {device_id}: "
                  f"{device.compute_capability}, {total_gb:.1f} GB total, {free_gb:.1f} GB free")

            if self._cuml_available:
                print(f"[GPU Backend] cuML available for GPU-accelerated ML")
            if self._cudf_available:
                print(f"[GPU Backend] cuDF available for GPU-accelerated DataFrames")

        except Exception as e:
            self._init_cpu_only(str(e))

    def _init_cpu_only(self, reason: str = "forced"):
        """Initialize CPU-only mode."""
        self._use_gpu = False
        self._cupy = None
        self._cuml_available = False
        self._cudf_available = False
        print(f"[GPU Backend] Using CPU mode ({reason})")

    @property
    def xp(self):
        """Return the array module (cupy or numpy)."""
        if self._use_gpu:
            return self._cupy
        return np

    @property
    def use_gpu(self) -> bool:
        """Check if GPU is being used."""
        return self._use_gpu

    @property
    def has_cuml(self) -> bool:
        """Check if cuML is available."""
        return self._cuml_available

    @property
    def has_cudf(self) -> bool:
        """Check if cuDF is available."""
        return self._cudf_available

    # ===== Array Creation =====

    def array(self, data, dtype=None):
        """Create array on GPU (or CPU if GPU not available)."""
        if self._use_gpu:
            return self._cupy.array(data, dtype=dtype)
        return np.array(data, dtype=dtype)

    def zeros(self, shape, dtype=np.float64):
        """Create zeros array."""
        return self.xp.zeros(shape, dtype=dtype)

    def ones(self, shape, dtype=np.float64):
        """Create ones array."""
        return self.xp.ones(shape, dtype=dtype)

    def empty(self, shape, dtype=np.float64):
        """Create empty array."""
        return self.xp.empty(shape, dtype=dtype)

    def arange(self, *args, **kwargs):
        """Create range array."""
        return self.xp.arange(*args, **kwargs)

    def linspace(self, *args, **kwargs):
        """Create linearly spaced array."""
        return self.xp.linspace(*args, **kwargs)

    def full(self, shape, fill_value, dtype=None):
        """Create filled array."""
        return self.xp.full(shape, fill_value, dtype=dtype)

    def asarray(self, data, dtype=None):
        """Convert to array."""
        if self._use_gpu:
            if isinstance(data, self._cupy.ndarray):
                return data if dtype is None else data.astype(dtype)
            return self._cupy.asarray(data, dtype=dtype)
        return np.asarray(data, dtype=dtype)

    # ===== Data Transfer =====

    def to_gpu(self, data):
        """Transfer data to GPU."""
        if self._use_gpu:
            if isinstance(data, self._cupy.ndarray):
                return data
            return self._cupy.asarray(data)
        return np.asarray(data)

    def to_numpy(self, data):
        """Transfer data to CPU (NumPy)."""
        if self._use_gpu and isinstance(data, self._cupy.ndarray):
            return self._cupy.asnumpy(data)
        return np.asarray(data)

    def to_cpu(self, data):
        """Alias for to_numpy."""
        return self.to_numpy(data)

    # ===== Math Operations =====

    def sqrt(self, x):
        return self.xp.sqrt(x)

    def exp(self, x):
        return self.xp.exp(x)

    def log(self, x):
        return self.xp.log(x)

    def sin(self, x):
        return self.xp.sin(x)

    def cos(self, x):
        return self.xp.cos(x)

    def arctan2(self, y, x):
        return self.xp.arctan2(y, x)

    def arccos(self, x):
        return self.xp.arccos(x)

    def clip(self, x, a_min, a_max):
        return self.xp.clip(x, a_min, a_max)

    def abs(self, x):
        return self.xp.abs(x)

    def sum(self, x, axis=None):
        return self.xp.sum(x, axis=axis)

    def mean(self, x, axis=None):
        return self.xp.mean(x, axis=axis)

    def std(self, x, axis=None, ddof=0):
        return self.xp.std(x, axis=axis, ddof=ddof)

    def median(self, x, axis=None):
        return self.xp.median(x, axis=axis)

    def max(self, x, axis=None):
        return self.xp.max(x, axis=axis)

    def min(self, x, axis=None):
        return self.xp.min(x, axis=axis)

    def argmax(self, x, axis=None):
        return self.xp.argmax(x, axis=axis)

    def argmin(self, x, axis=None):
        return self.xp.argmin(x, axis=axis)

    def argsort(self, x, axis=-1):
        return self.xp.argsort(x, axis=axis)

    def sort(self, x, axis=-1):
        return self.xp.sort(x, axis=axis)

    def unique(self, x, return_counts=False):
        return self.xp.unique(x, return_counts=return_counts)

    def where(self, condition, x=None, y=None):
        if x is None and y is None:
            return self.xp.where(condition)
        return self.xp.where(condition, x, y)

    def diff(self, x, n=1, axis=-1):
        return self.xp.diff(x, n=n, axis=axis)

    # ===== Linear Algebra =====

    def dot(self, a, b):
        return self.xp.dot(a, b)

    def matmul(self, a, b):
        return self.xp.matmul(a, b)

    def outer(self, a, b):
        return self.xp.outer(a, b)

    def norm(self, x, axis=None, ord=None):
        return self.xp.linalg.norm(x, axis=axis, ord=ord)

    def svd(self, a, full_matrices=True):
        return self.xp.linalg.svd(a, full_matrices=full_matrices)

    def lstsq(self, a, b, rcond=None):
        if self._use_gpu:
            return self._cupy.linalg.lstsq(a, b, rcond=rcond)
        return np.linalg.lstsq(a, b, rcond=rcond)

    def eigh(self, a):
        return self.xp.linalg.eigh(a)

    def eigvalsh(self, a):
        return self.xp.linalg.eigvalsh(a)

    def cov(self, m, rowvar=True):
        return self.xp.cov(m, rowvar=rowvar)

    # ===== Array Manipulation =====

    def column_stack(self, tup):
        return self.xp.column_stack(tup)

    def row_stack(self, tup):
        return self.xp.row_stack(tup)

    def concatenate(self, arrays, axis=0):
        return self.xp.concatenate(arrays, axis=axis)

    def stack(self, arrays, axis=0):
        return self.xp.stack(arrays, axis=axis)

    def reshape(self, x, shape):
        return self.xp.reshape(x, shape)

    def transpose(self, x, axes=None):
        return self.xp.transpose(x, axes=axes)

    def squeeze(self, x, axis=None):
        return self.xp.squeeze(x, axis=axis)

    def expand_dims(self, x, axis):
        return self.xp.expand_dims(x, axis=axis)

    # ===== Random =====

    def random_seed(self, seed: int):
        """Set random seed."""
        if self._use_gpu:
            self._cupy.random.seed(seed)
        np.random.seed(seed)

    def random_normal(self, loc=0.0, scale=1.0, size=None):
        return self.xp.random.normal(loc, scale, size)

    def random_uniform(self, low=0.0, high=1.0, size=None):
        return self.xp.random.uniform(low, high, size)

    def random_choice(self, a, size=None, replace=True, p=None):
        if self._use_gpu:
            # CuPy random choice has limitations
            a_np = self.to_numpy(a) if isinstance(a, self._cupy.ndarray) else a
            p_np = self.to_numpy(p) if p is not None and isinstance(p, self._cupy.ndarray) else p
            result = np.random.choice(a_np, size=size, replace=replace, p=p_np)
            return self._cupy.asarray(result)
        return np.random.choice(a, size=size, replace=replace, p=p)

    # ===== Memory Management =====

    def memory_info(self) -> Tuple[int, int]:
        """Get GPU memory info (free, total) in bytes."""
        if self._use_gpu:
            device = self._cupy.cuda.Device(self.device_id)
            return device.mem_info
        return (0, 0)

    def clear_memory(self):
        """Clear GPU memory pool."""
        if self._use_gpu:
            mempool = self._cupy.get_default_memory_pool()
            pinned_mempool = self._cupy.get_default_pinned_memory_pool()
            mempool.free_all_blocks()
            pinned_mempool.free_all_blocks()

    def sync(self):
        """Synchronize GPU operations."""
        if self._use_gpu:
            self._cupy.cuda.Stream.null.synchronize()


def get_backend(device_id: int = 0, reinit: bool = False) -> GPUBackend:
    """
    Get the global GPU backend instance.

    Args:
        device_id: CUDA device ID.
        reinit: Force reinitialization.

    Returns:
        GPUBackend instance.
    """
    global _backend_instance

    if _backend_instance is None or reinit:
        _backend_instance = GPUBackend(device_id=device_id)

    return _backend_instance


# Convenience module-level functions
def xp():
    """Get the array module (cupy or numpy)."""
    return get_backend().xp


def use_gpu() -> bool:
    """Check if GPU is being used."""
    return get_backend().use_gpu


def to_numpy(data):
    """Transfer data to CPU."""
    return get_backend().to_numpy(data)


def to_gpu(data):
    """Transfer data to GPU."""
    return get_backend().to_gpu(data)


if __name__ == "__main__":
    # Test GPU backend
    gpu = get_backend()

    print(f"\nGPU available: {gpu.use_gpu}")
    print(f"cuML available: {gpu.has_cuml}")
    print(f"cuDF available: {gpu.has_cudf}")

    # Test array operations
    x = gpu.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = gpu.sqrt(x**2 + 1)

    print(f"\nArray type: {type(x)}")
    print(f"x = {gpu.to_numpy(x)}")
    print(f"sqrt(x^2 + 1) = {gpu.to_numpy(y)}")

    # Test linear algebra
    A = gpu.array([[1, 2], [3, 4], [5, 6]])
    U, s, Vt = gpu.svd(A, full_matrices=False)
    print(f"\nSVD singular values: {gpu.to_numpy(s)}")

    # Memory info
    if gpu.use_gpu:
        free, total = gpu.memory_info()
        print(f"\nGPU Memory: {free/1e9:.2f} GB free / {total/1e9:.2f} GB total")
