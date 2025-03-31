import struct
import numpy as np


class DataSerializer:
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
    }

    def __init__(self, value):
        """Initialize the serializer with a single value (not a list/dict)."""
        self.value = value
        self.array_shapes = {}  # Store array shapes for unpacking
        self.format_string, self.serialized_value = self._create_format_string_and_value()

    def _create_format_string_and_value(self):
        """Determine struct format and serialize the value."""
        format_string = "<"  # Little-endian
        serialized_value = ()

        # # Handle Standard Python Scalars
        if isinstance(self.value, (int, float, bool)):
            # print("(int, float, bool)")
            struct_format = self.c_to_struct_format[self.type_conversion_dict[type(self.value)]]
            format_string += struct_format
            serialized_value = (self.value,)
            return format_string, serialized_value

        # Handle Strings (Null-Terminated for C Compatibility)
        if isinstance(self.value, str):
            # print("str")
            string_bytes = self.value.encode("utf-8") + b"\x00"
            format_string += f"{len(string_bytes)}s"
            serialized_value = (string_bytes,)
            return format_string, serialized_value

        # Handle NumPy Arrays
        if isinstance(self.value, np.ndarray):
            dtype_name = f"numpy.{self.value.dtype.name}"
            # print(dtype_name)
            if dtype_name in self.type_conversion_dict:
                struct_format = self.c_to_struct_format[self.type_conversion_dict[dtype_name]]
                flattened_value = self.value.flatten()
                format_string += f"{len(flattened_value)}{struct_format}"
                serialized_value = tuple(flattened_value.tolist())  # Convert array to tuple
            return format_string, serialized_value

        # Handle NumPy Scalars
        if isinstance(self.value, np.ScalarType):
            dtype_name = f"numpy.{self.value.dtype.name}"
            # print(dtype_name)
            if dtype_name in self.type_conversion_dict:
                struct_format = self.c_to_struct_format[self.type_conversion_dict[dtype_name]]
                format_string += struct_format
                serialized_value = (self.value,)
            return format_string, serialized_value

        # If no valid type found, raise an error
        raise TypeError(f"Unsupported type: {type(self.value)}")

    def pack(self)-> bytes:
        # print(f"{self.format_string=}")
        """Pack the single value into bytes."""
        return struct.pack(self.format_string, *self.serialized_value)

    def unpack(self, packed_data):
        """Unpack bytes into a single value matching the original format."""
        if not packed_data or not self.format_string:
            return None  # Handle case where nothing is packed

        unpacked_value = struct.unpack(self.format_string, packed_data)

        if isinstance(self.value, np.ndarray):
            return np.array(unpacked_value, dtype=self.value.dtype).reshape(self.value.shape)

        if isinstance(self.value, str):
            return unpacked_value[0].decode("utf-8").rstrip("\x00")

        return unpacked_value[0]  # Return the unpacked scalar

    @property
    def size(self):
        """Returns the total packed size in bytes."""
        return struct.calcsize(self.format_string) if self.format_string else 0

    def __str__(self):
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
    }

    for name, value in test_values.items():
        print(f"\nTesting: {name}")

        ds = DataSerializer(value)
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
