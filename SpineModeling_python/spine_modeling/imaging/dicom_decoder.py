"""
DICOM Decoder Module

This module provides low-level DICOM file parsing functionality for reading DICOM
medical image files. It handles binary file reading, tag parsing with Value Representation
(VR) decoding, and pixel data extraction for various bit depths (8, 16, 24-bit).

The DicomDecoder class implements a complete DICOM file parser that:
- Detects DICOM file types (DICOM 3.0, older DICOM, or non-DICOM)
- Handles endianness (little-endian and big-endian transfer syntaxes)
- Parses DICOM tags and extracts metadata
- Extracts pixel data for 8-bit, 16-bit (signed/unsigned), and 24-bit (RGB) images
- Applies rescale slope/intercept and window center/width transformations
- Supports color lookup tables (LUT) for palette images

Note: This is a low-level implementation. For most use cases, consider using
      pydicom library instead, which provides higher-level DICOM file access.
      This module is preserved for compatibility with the C# implementation.

Example Usage:
    >>> decoder = DicomDecoder()
    >>> decoder.dicom_file_name = "/path/to/image.dcm"
    >>> if decoder.type_of_dicom_file == TypeOfDicomFile.DICOM3_FILE:
    ...     pixels = decoder.get_pixels_16()
    ...     print(f"Image size: {decoder.width} x {decoder.height}")
    ...     print(f"Bits allocated: {decoder.bits_allocated}")

"""

import struct
import os
from enum import Enum
from typing import List, Optional, Tuple
from .dicom_dictionary import DicomDictionary


class ImageBitsPerPixel(Enum):
    """Enumeration of supported bits per pixel for image data."""
    EIGHT = 8
    SIXTEEN = 16
    TWENTY_FOUR = 24


class ViewSettings(Enum):
    """Enumeration of view/zoom settings."""
    ZOOM_1_1 = "1:1"
    ZOOM_TO_FIT = "fit"


class TypeOfDicomFile(Enum):
    """Enumeration of DICOM file types."""
    NOT_DICOM = 0
    DICOM3_FILE = 1
    DICOM_OLD_TYPE_FILE = 2
    DICOM_UNKNOWN_TRANSFER_SYNTAX = 3


class DicomDecoder:
    """
    Low-level DICOM file decoder for reading and parsing DICOM medical images.

    This class provides comprehensive DICOM file parsing including:
    - File format detection (DICOM 3.0 vs older formats)
    - Binary tag and metadata parsing
    - Pixel data extraction (8/16/24-bit)
    - Endianness handling
    - Rescaling and windowing transformations

    Attributes:
        bits_allocated (int): Bits allocated per pixel (8, 16, or 24)
        width (int): Image width in pixels
        height (int): Image height in pixels
        offset (int): Byte offset to pixel data in file
        n_images (int): Number of frames/images in file
        samples_per_pixel (int): Samples per pixel (1=grayscale, 3=RGB)
        pixel_depth (float): Slice thickness in mm
        pixel_width (float): Pixel width in mm
        pixel_height (float): Pixel height in mm
        unit (str): Unit of measurement (typically "mm")
        window_centre (float): Window center for display
        window_width (float): Window width for display
        signed_image (bool): Whether image contains signed pixel values
        type_of_dicom_file (TypeOfDicomFile): Detected DICOM file type
        dicom_info (List[str]): List of parsed DICOM tags and values
        dicm_found (bool): Whether "DICM" prefix was found at offset 128

    """

    # DICOM tag constants
    PIXEL_REPRESENTATION = 0x00280103
    TRANSFER_SYNTAX_UID = 0x00020010
    MODALITY = 0x00080060
    SLICE_THICKNESS = 0x00180050
    SLICE_SPACING = 0x00180088
    SAMPLES_PER_PIXEL = 0x00280002
    PHOTOMETRIC_INTERPRETATION = 0x00280004
    PLANAR_CONFIGURATION = 0x00280006
    NUMBER_OF_FRAMES = 0x00280008
    ROWS = 0x00280010
    COLUMNS = 0x00280011
    PIXEL_SPACING = 0x00280030
    BITS_ALLOCATED = 0x00280100
    WINDOW_CENTER = 0x00281050
    WINDOW_WIDTH = 0x00281051
    RESCALE_INTERCEPT = 0x00281052
    RESCALE_SLOPE = 0x00281053
    RED_PALETTE = 0x00281201
    GREEN_PALETTE = 0x00281202
    BLUE_PALETTE = 0x00281203
    ICON_IMAGE_SEQUENCE = 0x00880200
    PIXEL_DATA = 0x7FE00010

    # Special item tags
    ITEM = "FFFEE000"
    ITEM_DELIMITATION = "FFFEE00D"
    SEQUENCE_DELIMITATION = "FFFEE0DD"

    # Value Representation (VR) constants
    VR_AE = 0x4145
    VR_AS = 0x4153
    VR_AT = 0x4154
    VR_CS = 0x4353
    VR_DA = 0x4441
    VR_DS = 0x4453
    VR_DT = 0x4454
    VR_FD = 0x4644
    VR_FL = 0x464C
    VR_IS = 0x4953
    VR_LO = 0x4C4F
    VR_LT = 0x4C54
    VR_PN = 0x504E
    VR_SH = 0x5348
    VR_SL = 0x534C
    VR_SS = 0x5353
    VR_ST = 0x5354
    VR_TM = 0x544D
    VR_UI = 0x5549
    VR_UL = 0x554C
    VR_US = 0x5553
    VR_UT = 0x5554
    VR_OB = 0x4F42
    VR_OW = 0x4F57
    VR_SQ = 0x5351
    VR_UN = 0x554E
    VR_QQ = 0x3F3F
    VR_RT = 0x5254

    ID_OFFSET = 128  # Location of "DICM" prefix
    IMPLICIT_VR = 0x2D2D  # '--'
    DICM = "DICM"

    def __init__(self):
        """Initialize DICOM decoder with default values."""
        self.dic = DicomDictionary()
        self.signed_image = False
        self.dicom_info = []
        self.dicm_found = False

        # File reading state
        self._file = None
        self._dicom_file_name = ""
        self._little_endian = True
        self._odd_locations = False
        self._big_endian_transfer_syntax = False
        self._in_sequence = False
        self._width_tag_found = False
        self._height_tag_found = False
        self._pixel_data_tag_found = False
        self._location = 0
        self._element_length = 0
        self._vr = 0
        self._photo_interpretation = ""

        # Image properties
        self.bits_allocated = 0
        self.width = 1
        self.height = 1
        self.offset = 1
        self.n_images = 1
        self.samples_per_pixel = 1
        self.pixel_depth = 1.0
        self.pixel_width = 1.0
        self.pixel_height = 1.0
        self.unit = "mm"
        self.window_centre = 0.0
        self.window_width = 0.0
        self.type_of_dicom_file = TypeOfDicomFile.NOT_DICOM

        # Pixel data storage
        self._pixels_8 = None
        self._pixels_16 = None
        self._pixels_24 = None
        self._pixels_16_int = None

        # Rescaling parameters
        self._pixel_representation = 0
        self._rescale_intercept = 0.0
        self._rescale_slope = 1.0

        # Color lookup tables
        self._reds = None
        self._greens = None
        self._blues = None

        # Min/max values for different bit depths
        self._min_8 = 0
        self._max_8 = 255
        self._min_16 = -32768
        self._max_16 = 65535

        self._initialize_dicom()

    def _initialize_dicom(self):
        """Reset DICOM decoder state for reading a new file."""
        self.bits_allocated = 0
        self.width = 1
        self.height = 1
        self.offset = 1
        self.n_images = 1
        self.samples_per_pixel = 1
        self._photo_interpretation = ""
        self.unit = "mm"
        self.window_centre = 0.0
        self.window_width = 0.0
        self.signed_image = False
        self._width_tag_found = False
        self._height_tag_found = False
        self._pixel_data_tag_found = False
        self._rescale_intercept = 0.0
        self._rescale_slope = 1.0
        self.type_of_dicom_file = TypeOfDicomFile.NOT_DICOM

    @property
    def dicom_file_name(self) -> str:
        """Get the current DICOM file name."""
        return self._dicom_file_name

    @dicom_file_name.setter
    def dicom_file_name(self, value: str):
        """
        Set DICOM file name and automatically parse the file.

        Args:
            value: Path to DICOM file

        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file cannot be read

        """
        self._dicom_file_name = value
        self._initialize_dicom()
        self.dicom_info.clear()
        self._location = 0

        if not os.path.exists(value):
            raise FileNotFoundError(f"DICOM file not found: {value}")

        try:
            with open(value, 'rb') as f:
                self._file = f
                read_result = self._read_file_info()

                if read_result and self._width_tag_found and self._height_tag_found and self._pixel_data_tag_found:
                    self._read_pixels()
                    if self.dicm_found:
                        self.type_of_dicom_file = TypeOfDicomFile.DICOM3_FILE
                    else:
                        self.type_of_dicom_file = TypeOfDicomFile.DICOM_OLD_TYPE_FILE
        except Exception as e:
            print(f"Error reading DICOM file: {e}")
        finally:
            self._file = None

    def get_pixels_8(self) -> Optional[List[int]]:
        """
        Get 8-bit pixel data.

        Returns:
            List of 8-bit pixel values, or None if not available

        """
        return self._pixels_8

    def get_pixels_16(self) -> Optional[List[int]]:
        """
        Get 16-bit pixel data.

        Returns:
            List of 16-bit pixel values, or None if not available

        """
        return self._pixels_16

    def get_pixels_24(self) -> Optional[List[int]]:
        """
        Get 24-bit RGB pixel data.

        Returns:
            List of 8-bit RGB values (R,G,B,R,G,B,...), or None if not available

        """
        return self._pixels_24

    def _get_string(self, length: int) -> str:
        """Read ASCII string from file."""
        if self._file is None:
            return ""
        self._file.seek(self._location)
        data = self._file.read(length)
        self._location += length
        return data.decode('ascii', errors='ignore')

    def _get_byte(self) -> int:
        """Read single byte from file."""
        if self._file is None:
            return 0
        self._file.seek(self._location)
        byte = self._file.read(1)
        self._location += 1
        return byte[0] if byte else 0

    def _get_short(self) -> int:
        """Read 16-bit unsigned short from file."""
        b0 = self._get_byte()
        b1 = self._get_byte()
        if self._little_endian:
            return (b1 << 8) + b0
        else:
            return (b0 << 8) + b1

    def _get_int(self) -> int:
        """Read 32-bit integer from file."""
        b0 = self._get_byte()
        b1 = self._get_byte()
        b2 = self._get_byte()
        b3 = self._get_byte()
        if self._little_endian:
            return (b3 << 24) + (b2 << 16) + (b1 << 8) + b0
        else:
            return (b0 << 24) + (b1 << 16) + (b2 << 8) + b3

    def _get_double(self) -> float:
        """Read 64-bit double from file."""
        bytes_list = [self._get_byte() for _ in range(8)]
        if self._little_endian:
            bytes_data = bytes(bytes_list)
        else:
            bytes_data = bytes(reversed(bytes_list))
        return struct.unpack('<d', bytes_data)[0]

    def _get_float(self) -> float:
        """Read 32-bit float from file."""
        bytes_list = [self._get_byte() for _ in range(4)]
        if self._little_endian:
            bytes_data = bytes(bytes_list)
        else:
            bytes_data = bytes(reversed(bytes_list))
        return struct.unpack('<f', bytes_data)[0]

    def _get_lut(self, length: int) -> Optional[List[int]]:
        """Read color lookup table."""
        if (length & 1) != 0:  # odd length
            _ = self._get_string(length)
            return None

        length //= 2
        lut = []
        for _ in range(length):
            lut.append(self._get_short() >> 8)
        return lut

    def _get_length(self) -> int:
        """
        Parse Value Representation (VR) and element length from DICOM tag.

        Returns:
            Element length in bytes

        """
        b0 = self._get_byte()
        b1 = self._get_byte()
        b2 = self._get_byte()
        b3 = self._get_byte()

        self._vr = (b0 << 8) + b1

        # Check for explicit VR with 32-bit length
        if self._vr in [self.VR_OB, self.VR_OW, self.VR_SQ, self.VR_UN, self.VR_UT]:
            if b2 == 0 or b3 == 0:
                return self._get_int()
            # Implicit VR with 32-bit length
            self._vr = self.IMPLICIT_VR
            if self._little_endian:
                return (b3 << 24) + (b2 << 16) + (b1 << 8) + b0
            else:
                return (b0 << 24) + (b1 << 16) + (b2 << 8) + b3

        # Explicit VR with 16-bit length
        if self._vr in [self.VR_AE, self.VR_AS, self.VR_AT, self.VR_CS, self.VR_DA, self.VR_DS,
                        self.VR_DT, self.VR_FD, self.VR_FL, self.VR_IS, self.VR_LO, self.VR_LT,
                        self.VR_PN, self.VR_SH, self.VR_SL, self.VR_SS, self.VR_ST, self.VR_TM,
                        self.VR_UI, self.VR_UL, self.VR_US, self.VR_QQ, self.VR_RT]:
            if self._little_endian:
                return (b3 << 8) + b2
            else:
                return (b2 << 8) + b3

        # Default: Implicit VR with 32-bit length
        self._vr = self.IMPLICIT_VR
        if self._little_endian:
            return (b3 << 24) + (b2 << 16) + (b1 << 8) + b0
        else:
            return (b0 << 24) + (b1 << 16) + (b2 << 8) + b3

    def _get_next_tag(self) -> int:
        """
        Read next DICOM tag from file.

        Returns:
            32-bit tag value (group << 16 | element)

        """
        group_word = self._get_short()

        # Handle big-endian transfer syntax detection
        if group_word == 0x0800 and self._big_endian_transfer_syntax:
            self._little_endian = False
            group_word = 0x0008

        element_word = self._get_short()
        tag = (group_word << 16) | element_word

        self._element_length = self._get_length()

        # Hack to read some GE files
        if self._element_length == 13 and not self._odd_locations:
            self._element_length = 10

        # "Undefined" element length indicates sequence
        if self._element_length == -1:
            self._element_length = 0
            self._in_sequence = True

        return tag

    def _get_header_info(self, tag: int, value: Optional[str]) -> Optional[str]:
        """
        Format DICOM tag information for display.

        Args:
            tag: DICOM tag value
            value: Tag value string, or None to read from file

        Returns:
            Formatted tag information string, or None if tag should be skipped

        """
        tag_str = f"{tag:08X}"

        # Check for sequence delimiters
        if tag_str in [self.ITEM_DELIMITATION, self.SEQUENCE_DELIMITATION]:
            self._in_sequence = False
            return None

        # Look up tag in dictionary
        tag_id = None
        if self.dic.contains_tag(tag_str):
            tag_id = self.dic.get_tag(tag_str)
            if tag_id and self._vr == self.IMPLICIT_VR:
                # Extract VR from dictionary
                self._vr = (ord(tag_id[0]) << 8) + ord(tag_id[1])
            if tag_id:
                tag_id = tag_id[2:]  # Remove VR prefix

        if tag_str == self.ITEM:
            return tag_id if tag_id else ":null"

        if value is not None:
            return f"{tag_id}: {value}" if tag_id else f"---: {value}"

        # Read value based on VR
        if self._vr in [self.VR_FD, self.VR_FL]:
            for _ in range(self._element_length):
                self._get_byte()
        elif self._vr in [self.VR_AE, self.VR_AS, self.VR_AT, self.VR_CS, self.VR_DA, self.VR_DS,
                          self.VR_DT, self.VR_IS, self.VR_LO, self.VR_LT, self.VR_PN, self.VR_SH,
                          self.VR_ST, self.VR_TM, self.VR_UI]:
            value = self._get_string(self._element_length)
        elif self._vr == self.VR_US:
            if self._element_length == 2:
                value = str(self._get_short())
            else:
                values = []
                n = self._element_length // 2
                for _ in range(n):
                    values.append(str(self._get_short()))
                value = " ".join(values)
        elif self._vr == self.IMPLICIT_VR:
            value = self._get_string(self._element_length)
            if self._element_length > 44:
                value = None
        elif self._vr == self.VR_SQ:
            value = ""
            private_tag = ((tag >> 16) & 1) != 0
            if tag != self.ICON_IMAGE_SEQUENCE and not private_tag:
                pass
            else:
                self._location += self._element_length
                value = ""
        else:
            self._location += self._element_length
            value = ""

        if value and not tag_id and value:
            return f"---: {value}"
        elif not tag_id:
            return None
        else:
            return f"{tag_id}: {value}"

    def _add_info(self, tag: int, value=None):
        """
        Add DICOM tag information to info list.

        Args:
            tag: DICOM tag value
            value: Tag value (string or int), or None to read from file

        """
        if value is not None and not isinstance(value, str):
            value = str(value)

        info = self._get_header_info(tag, value)
        tag_str = f"{tag:08X}"

        if self._in_sequence and info and self._vr != self.VR_SQ:
            info = f">{info}"

        if info and tag_str != self.ITEM:
            if "---" in info:
                info = info.replace("---", "Private Tag")
            self.dicom_info.append(f"{tag_str}//{info}")

    def _get_spatial_scale(self, scale_str: str):
        """
        Parse pixel spacing from DICOM tag value.

        Args:
            scale_str: Pixel spacing string (format: "row_spacing\\col_spacing")

        """
        try:
            parts = scale_str.split('\\')
            if len(parts) == 2:
                yscale = float(parts[0])
                xscale = float(parts[1])
                if xscale != 0.0 and yscale != 0.0:
                    self.pixel_width = xscale
                    self.pixel_height = yscale
                    self.unit = "mm"
        except (ValueError, IndexError):
            pass

    def _read_file_info(self) -> bool:
        """
        Read and parse DICOM file header information.

        Returns:
            True if file was successfully parsed, False otherwise

        """
        if self._file is None:
            return False

        self._file.seek(self.ID_OFFSET)
        self._location = self.ID_OFFSET
        self.bits_allocated = 16

        # Check for "DICM" prefix at offset 128
        dicm_str = self._get_string(4)
        if dicm_str != self.DICM:
            # Older DICOM file (before 3.0) - no preamble
            self._file.seek(0)
            self._location = 0
            self.dicm_found = False
        else:
            # DICOM 3.0 file
            self.dicm_found = True

        decoding_tags = True
        self.samples_per_pixel = 1
        planar_configuration = 0
        self._photo_interpretation = ""

        while decoding_tags:
            tag = self._get_next_tag()

            if (self._location & 1) != 0:
                self._odd_locations = True

            if self._in_sequence:
                self._add_info(tag, None)
                continue

            # Process specific tags
            if tag == self.TRANSFER_SYNTAX_UID:
                s = self._get_string(self._element_length)
                self._add_info(tag, s)
                if "1.2.4" in s or "1.2.5" in s:
                    self.type_of_dicom_file = TypeOfDicomFile.DICOM_UNKNOWN_TRANSFER_SYNTAX
                    return False
                if "1.2.840.10008.1.2.2" in s:
                    self._big_endian_transfer_syntax = True

            elif tag == self.MODALITY:
                modality = self._get_string(self._element_length)
                self._add_info(tag, modality)

            elif tag == self.NUMBER_OF_FRAMES:
                s = self._get_string(self._element_length)
                self._add_info(tag, s)
                try:
                    frames = float(s)
                    if frames > 1.0:
                        self.n_images = int(frames)
                except ValueError:
                    pass

            elif tag == self.SAMPLES_PER_PIXEL:
                self.samples_per_pixel = self._get_short()
                self._add_info(tag, self.samples_per_pixel)

            elif tag == self.PHOTOMETRIC_INTERPRETATION:
                self._photo_interpretation = self._get_string(self._element_length).strip()
                self._add_info(tag, self._photo_interpretation)

            elif tag == self.PLANAR_CONFIGURATION:
                planar_configuration = self._get_short()
                self._add_info(tag, planar_configuration)

            elif tag == self.ROWS:
                self.height = self._get_short()
                self._add_info(tag, self.height)
                self._height_tag_found = True

            elif tag == self.COLUMNS:
                self.width = self._get_short()
                self._add_info(tag, self.width)
                self._width_tag_found = True

            elif tag == self.PIXEL_SPACING:
                scale = self._get_string(self._element_length)
                self._get_spatial_scale(scale)
                self._add_info(tag, scale)

            elif tag in [self.SLICE_THICKNESS, self.SLICE_SPACING]:
                spacing = self._get_string(self._element_length)
                try:
                    self.pixel_depth = float(spacing)
                except ValueError:
                    pass
                self._add_info(tag, spacing)

            elif tag == self.BITS_ALLOCATED:
                self.bits_allocated = self._get_short()
                self._add_info(tag, self.bits_allocated)

            elif tag == self.PIXEL_REPRESENTATION:
                self._pixel_representation = self._get_short()
                self._add_info(tag, self._pixel_representation)

            elif tag == self.WINDOW_CENTER:
                center = self._get_string(self._element_length)
                if '\\' in center:
                    center = center.split('\\')[-1]
                try:
                    self.window_centre = float(center)
                except ValueError:
                    pass
                self._add_info(tag, center)

            elif tag == self.WINDOW_WIDTH:
                width_str = self._get_string(self._element_length)
                if '\\' in width_str:
                    width_str = width_str.split('\\')[-1]
                try:
                    self.window_width = float(width_str)
                except ValueError:
                    pass
                self._add_info(tag, width_str)

            elif tag == self.RESCALE_INTERCEPT:
                intercept = self._get_string(self._element_length)
                try:
                    self._rescale_intercept = float(intercept)
                except ValueError:
                    pass
                self._add_info(tag, intercept)

            elif tag == self.RESCALE_SLOPE:
                slope = self._get_string(self._element_length)
                try:
                    self._rescale_slope = float(slope)
                except ValueError:
                    pass
                self._add_info(tag, slope)

            elif tag == self.RED_PALETTE:
                self._reds = self._get_lut(self._element_length)
                self._add_info(tag, self._element_length // 2)

            elif tag == self.GREEN_PALETTE:
                self._greens = self._get_lut(self._element_length)
                self._add_info(tag, self._element_length // 2)

            elif tag == self.BLUE_PALETTE:
                self._blues = self._get_lut(self._element_length)
                self._add_info(tag, self._element_length // 2)

            elif tag == self.PIXEL_DATA:
                if self._element_length != 0:
                    self.offset = self._location
                    self._add_info(tag, self._location)
                    decoding_tags = False
                else:
                    self._add_info(tag, None)
                self._pixel_data_tag_found = True

            else:
                self._add_info(tag, None)

        return True

    def _read_pixels(self):
        """Read and process pixel data from DICOM file."""
        if self._file is None:
            return

        # 8-bit grayscale
        if self.samples_per_pixel == 1 and self.bits_allocated == 8:
            self._pixels_8 = []
            num_pixels = self.width * self.height
            self._file.seek(self.offset)
            buf = self._file.read(num_pixels)

            for i in range(num_pixels):
                pix_val = int(buf[i] * self._rescale_slope + self._rescale_intercept)
                if self._photo_interpretation == "MONOCHROME1":
                    pix_val = self._max_8 - pix_val
                if self._pixel_representation == 1:
                    self._pixels_8.append(pix_val)
                else:
                    self._pixels_8.append(pix_val - self._min_8)

        # 16-bit grayscale
        elif self.samples_per_pixel == 1 and self.bits_allocated == 16:
            self._pixels_16 = []
            self._pixels_16_int = []
            num_pixels = self.width * self.height
            self._file.seek(self.offset)
            buf_byte = self._file.read(num_pixels * 2)

            for i in range(num_pixels):
                i1 = i * 2
                b0 = buf_byte[i1]
                b1 = buf_byte[i1 + 1]
                unsigned_s = (b1 << 8) + b0

                if self._pixel_representation == 0:  # Unsigned
                    pix_val = int(unsigned_s * self._rescale_slope + self._rescale_intercept)
                    if self._photo_interpretation == "MONOCHROME1":
                        pix_val = self._max_16 - pix_val
                else:  # Signed (2's complement)
                    signed_data = struct.pack('BB', b0, b1)
                    s_val = struct.unpack('<h', signed_data)[0]
                    pix_val = int(s_val * self._rescale_slope + self._rescale_intercept)
                    if self._photo_interpretation == "MONOCHROME1":
                        pix_val = self._max_16 - pix_val

                self._pixels_16_int.append(pix_val)

            # Check for signed values
            min_pix_val = min(self._pixels_16_int)
            self.signed_image = min_pix_val < 0

            # Normalize to 0-65535 range
            for pixel in self._pixels_16_int:
                if self.signed_image:
                    self._pixels_16.append(pixel - self._min_16)
                else:
                    self._pixels_16.append(pixel)

            self._pixels_16_int.clear()

        # 24-bit RGB
        elif self.samples_per_pixel == 3 and self.bits_allocated == 8:
            self.signed_image = False
            self._pixels_24 = []
            num_pixels = self.width * self.height
            num_bytes = num_pixels * self.samples_per_pixel
            self._file.seek(self.offset)
            buf = self._file.read(num_bytes)

            for i in range(num_bytes):
                self._pixels_24.append(buf[i])
