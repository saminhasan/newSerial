import struct
import numpy as np
from typing import Any, Tuple, Union

class Serializer:
    type_conversion_dict = {
        int: "int",
        float: "float",
        bool: "bool",
        "int8": "int8_t",
        "int16": "int16_t",
        "int32": "int32_t",
        "int64": "int64_t",
        "uint8": "uint8_t",
        "uint16": "uint16_t",
        "uint32": "uint32_t",
        "uint64": "uint64_t",
        "float32": "float",
        "float64": "double",
        "bool_": "bool",
        "numpy.int8": "int8_t",
        "numpy.int16": "int16_t",
        "numpy.int32": "int32_t",
        "numpy.int64": "int64_t",
        "numpy.uint8": "uint8_t",
        "numpy.uint16": "uint16_t",
        "numpy.uint32": "uint32_t",
        "numpy.uint64": "uint64_t",
        "numpy.float32": "float",
        "numpy.float64": "double",
        "numpy.bool_": "bool",
        "numpy.bool": "bool",
        "np.intc": "int",
        "np.intp": "intptr_t",
        "np.uintp": "uintptr_t",
        "np.short": "short",
        "np.ushort": "unsigned short",
        "np.longlong": "long long",
        "np.ulonglong": "unsigned long long",
        type(None): "None"
    }

    # Mapping C types to struct format characters
    c_to_struct_format = {
        "int": "i",
        "float": "f",
        "bool": "?",
        "int8_t": "b",
        "int16_t": "h",
        "int32_t": "i",
        "int64_t": "q",
        "uint8_t": "B",
        "uint16_t": "H",
        "uint32_t": "I",
        "uint64_t": "Q",
        "double": "d",
        "short": "h",
        "unsigned short": "H",
        "long long": "q",
        "unsigned long long": "Q",
        "intptr_t": "P",
        "uintptr_t": "P",
        "None": "NULL",
    }

    def __init__(self, value: Any) -> None:
        """Initialize the serializer with a single value (which can be nested)."""
        self.value = value
        # array_shapes is unused, so remove it if not needed.
        self.format_string, self.serialized_value = self._create_format_string_and_value()

    def _create_format_string_and_value(self) -> Tuple[str, Tuple]:
        body_fmt, serialized = self._serialize_value(self.value)
        return "<" + body_fmt, serialized

    def _serialize_value(self, value: Any) -> Tuple[str, Tuple]:
        match value:
            case None:
                return self._serialize_none(value)
            case int() | float() | bool():
                return self._serialize_scalar(value)
            case str():
                return self._serialize_str(value)
            case np.ndarray() as arr:
                return self._serialize_ndarray(arr)
            case _ if isinstance(value, np.ScalarType):
                return self._serialize_numpy_scalar(value)
            case list() | dict() | tuple():
                return self._serialize_iterable(value)
            case _:
                raise TypeError(f"Unsupported type: {type(value)}")

    def _serialize_none(self, value: None) -> Tuple[str, Tuple]:
        return "", ()

    def _serialize_scalar(self, value: Union[int, float, bool]) -> Tuple[str, Tuple]:
        c_type = self.type_conversion_dict[type(value)]
        struct_format = self.c_to_struct_format[c_type]
        return struct_format, (value,)

    def _serialize_str(self, value: str) -> Tuple[str, Tuple]:
        string_bytes = value.encode("utf-8") + b"\x00"
        return f"{len(string_bytes)}s", (string_bytes,)

    def _serialize_ndarray(self, arr: np.ndarray) -> Tuple[str, Tuple]:
        dtype_name = f"numpy.{arr.dtype.name}"
        if dtype_name in self.type_conversion_dict:
            struct_format = self.c_to_struct_format[self.type_conversion_dict[dtype_name]]
            flattened = arr.flatten()
            return f"{len(flattened)}{struct_format}", tuple(flattened.tolist())
        raise TypeError(f"Unsupported numpy dtype: {arr.dtype}")

    def _serialize_numpy_scalar(self, value: Any) -> Tuple[str, Tuple]:
        dtype_name = f"numpy.{value.dtype.name}"
        if dtype_name in self.type_conversion_dict:
            struct_format = self.c_to_struct_format[self.type_conversion_dict[dtype_name]]
            return struct_format, (value,)
        raise TypeError(f"Unsupported numpy scalar dtype: {value.dtype}")

    def _serialize_iterable(self, value: Union[list, dict, tuple]) -> Tuple[str, Tuple]:
        fmt_parts = []
        serialized_parts = []
        if isinstance(value, dict):
            # Iterate over dict values (in insertion order)
            for key, sub_value in value.items():
                sub_fmt, sub_serialized = self._serialize_value(sub_value)
                fmt_parts.append(sub_fmt)
                serialized_parts.extend(sub_serialized)
        else:
            for item in value:
                sub_fmt, sub_serialized = self._serialize_value(item)
                fmt_parts.append(sub_fmt)
                serialized_parts.extend(sub_serialized)
        return "".join(fmt_parts), tuple(serialized_parts)

    def pack(self) -> bytes:
        """Pack the value into bytes."""
        return struct.pack(self.format_string, *self.serialized_value)

    def unpack(self, packed_data: bytes) -> Any:
        """Unpack bytes into a value matching the original structure."""
        if not packed_data or not self.format_string:
            return None
        all_unpacked = struct.unpack(self.format_string, packed_data)
        if isinstance(self.value, (list, dict, tuple)):
            reconstructed, remaining = self._recursive_unpack(self.value, all_unpacked)
            if remaining:
                raise ValueError("Extra data found after unpacking.")
            return reconstructed
        if isinstance(self.value, np.ndarray):
            return np.array(all_unpacked, dtype=self.value.dtype).reshape(self.value.shape)
        if isinstance(self.value, str):
            return all_unpacked[0].decode("utf-8").rstrip("\x00")
        return all_unpacked[0]

    def _recursive_unpack(self, orig_value: Any, data_tuple: Tuple) -> Tuple[Any, Tuple]:
        """Recursively reconstruct the original structure from the flat tuple."""
        if isinstance(orig_value, list):
            result = []
            for item in orig_value:
                unpacked_item, data_tuple = self._recursive_unpack(item, data_tuple)
                result.append(unpacked_item)
            return result, data_tuple
        elif isinstance(orig_value, tuple):
            result = []
            for item in orig_value:
                unpacked_item, data_tuple = self._recursive_unpack(item, data_tuple)
                result.append(unpacked_item)
            return tuple(result), data_tuple
        elif isinstance(orig_value, dict):
            result = {}
            for key, val in orig_value.items():
                unpacked_item, data_tuple = self._recursive_unpack(val, data_tuple)
                result[key] = unpacked_item
            return result, data_tuple
        elif isinstance(orig_value, str):
            val = data_tuple[0]
            return val.decode("utf-8").rstrip("\x00"), data_tuple[1:]
        elif isinstance(orig_value, (int, float, bool)):
            return data_tuple[0], data_tuple[1:]
        elif isinstance(orig_value, np.ndarray):
            size = int(np.prod(orig_value.shape))
            dt = orig_value.dtype
            arr = np.array(data_tuple[:size], dtype=dt).reshape(orig_value.shape)
            return arr, data_tuple[size:]
        elif isinstance(orig_value, np.ScalarType):
            return data_tuple[0], data_tuple[1:]
        else:
            raise TypeError(f"Unsupported type in recursive unpack: {type(orig_value)}")

    @property
    def size(self) -> int:
        """Returns the total packed size in bytes."""
        return struct.calcsize(self.format_string) if self.format_string else 0

    def __str__(self) -> str:
        return f"DataSerializer(format={self.format_string}, value={self.value})"



def test():
    test_values = {
        "bool": True,
        "int": 42,
        "float": 3.14,
        "str": "Hello",
        # NumPy Scalars
        "np_bool": np.bool_(True),
        "np_int8": np.int8(-128),
        "np_uint8": np.uint8(255),
        "np_int16": np.int16(-32768),
        "np_uint16": np.uint16(65535),
        "np_int32": np.int32(-2147483648),
        "np_uint32": np.uint32(4294967295),
        "np_float32": np.float32(3.14),
        # NumPy Arrays (1D)
        "np_array_bool": np.array([True, False, True], dtype=np.bool_),
        "np_array_int8": np.array([-128, 127], dtype=np.int8),
        "np_array_uint8": np.array([0, 255], dtype=np.uint8),
        "np_array_int16": np.array([-32768, 32767], dtype=np.int16),
        "np_array_uint16": np.array([0, 65535], dtype=np.uint16),
        "np_array_int32": np.array([-2147483648, 2147483647], dtype=np.int32),
        "np_array_uint32": np.array([0, 4294967295], dtype=np.uint32),
        "np_array_float32": np.array([3.14, -2.71], dtype=np.float32),
        "list" : [np.uint8(1), np.float32(3.14), np.uint32(1000000), np.uint8(0x02)],
        "dict" : {'a' : 1,"adad" : "dawdaw"},
    }

    for name, value in test_values.items():
        print(f"\nTesting: {name}")

        ds = Serializer(value)
        packed_data = ds.pack()
        unpacked_value = ds.unpack(packed_data)

        print(f"Original Value: {value}")
        print(f"Packed Bytes: {packed_data.hex()}")
        print(f"Unpacked Value: {unpacked_value}")

        # Assertions to verify correctness
        if isinstance(value, np.ndarray):
            assert np.array_equal(unpacked_value, value), f"Test Failed: {name}"
        elif isinstance(value, float):
            assert np.isclose(unpacked_value, value, atol=1e-6), f"Test Failed: {name}"
        elif isinstance(value, str):
            assert unpacked_value == value, f"Test Failed: {name}"
        else:
            assert unpacked_value == value, f"Test Failed: {name}"

    print("\n All tests passed successfully!")


if __name__ == "__main__":
    test()
