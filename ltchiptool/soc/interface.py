# Copyright (c) Kuba Szczodrzyński 2022-07-29.

from abc import ABC
from io import FileIO
from typing import BinaryIO, Dict, Generator, List, Optional, Tuple, Union

from ltchiptool import Board, Family
from ltchiptool.util import graph
from uf2tool import UploadContext


class SocInterface(ABC):
    board: Board = None
    port: str = None
    baud: int = None
    link_timeout: float = 20.0
    read_timeout: float = 1.0

    @classmethod
    def get(cls, family: Family) -> "SocInterface":
        # fmt: off
        if family.parent_code == "bk72xx":
            from .bk72xx import BK72XXMain
            return BK72XXMain()
        if family.code == "ambz":
            from .ambz import AmebaZMain
            return AmebaZMain()
        # fmt: on
        raise NotImplementedError(f"Unsupported family - {family.name}")

    #########################
    # Common helper methods #
    #########################

    def set_board(self, board: Board):
        self.board = board
        if board:
            self.baud = self.baud or board["upload.speed"] or 115200

    def set_uart_params(
        self,
        port: str,
        baud: int = None,
        link_timeout: float = None,
        read_timeout: float = None,
    ):
        self.port = port or self.port
        self.baud = baud or self.baud or 115200
        self.link_timeout = link_timeout or self.link_timeout
        self.read_timeout = read_timeout or self.read_timeout

    def print_protocol(self):
        graph(1, f"Connecting on {self.port} @ {self.baud}")

    #####################################################
    # Abstract methods - implemented by the SoC modules #
    #####################################################

    def hello(self):
        raise NotImplementedError()

    @property
    def elf_has_dual_ota(self) -> bool:
        raise NotImplementedError()

    ##################################
    # Linking - ELF and BIN building #
    ##################################

    def link2elf(
        self,
        ota1: str,
        ota2: str,
        args: List[str],
    ) -> List[str]:
        raise NotImplementedError()

    def elf2bin(
        self,
        input: str,
        ota_idx: int,
    ) -> Dict[str, Optional[int]]:
        raise NotImplementedError()

    def link2bin(
        self,
        ota1: str,
        ota2: str,
        args: List[str],
    ) -> Dict[str, Optional[int]]:
        raise NotImplementedError()

    #########################################################
    # Flashing - reading/writing raw files and UF2 packages #
    #########################################################

    def flash_get_guide(self) -> List[Union[str, list]]:
        """Get a short textual guide for putting the chip in download mode."""
        raise NotImplementedError()

    def flash_hw_reset(self) -> None:
        """Perform a hardware reset using UART GPIO lines."""
        raise NotImplementedError()

    def flash_connect(self, force: bool = False) -> None:
        """Link with the chip for read/write operations. Do nothing if already linked or not supported."""
        raise NotImplementedError()

    def flash_get_chip_info_string(self) -> str:
        """Read chip info from the protocol as a string."""
        raise NotImplementedError()

    def flash_get_size(self) -> int:
        """Retrieve the flash size, in bytes."""
        raise NotImplementedError()

    def flash_get_file_type(
        self,
        file: FileIO,
        length: int,
    ) -> Optional[Tuple[str, Optional[int], int, int]]:
        """
        Check if the file is flashable to this SoC.

        :return: a tuple: (file type, start, skip, length), or None if type unknown
        """
        raise NotImplementedError()

    def flash_read_raw(
        self,
        start: int,
        length: int,
        verify: bool = True,
        use_rom: bool = False,
    ) -> Generator[bytes, None, None]:
        """
        Read 'length' bytes from offset 'start' of the flash.

        :return: a generator yielding the chunks being read
        """
        raise NotImplementedError()

    def flash_write_raw(
        self,
        start: int,
        length: int,
        data: BinaryIO,
        verify: bool = True,
    ) -> Generator[int, None, None]:
        """
        Write 'length' bytes (represented by 'data') to offset 'start' of the flash.

        :return: a generator yielding lengths of the chunks being written
        """
        raise NotImplementedError()

    def flash_write_uf2(
        self,
        ctx: UploadContext,
        verify: bool = True,
    ) -> Generator[Union[int, str], None, None]:
        """
        Upload an UF2 package to the chip.

        :return: a generator, yielding either the total writing length,
        then lengths of the chunks being written, or progress messages, as string
        """
        raise NotImplementedError()
