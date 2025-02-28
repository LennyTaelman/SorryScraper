import os
from pathlib import Path
from typing import List, Union

from pydantic import BaseModel

from sorrydb.database.sorry import Sorry


class SorryDatabase(BaseModel):
    """A simple json database for collections of Sorry objects."""

    sorries: List[Sorry] = []

    def add_sorries(self, sorries: List[Sorry]) -> None:
        """Add multiple Sorry objects to the database.

        Args:
            sorries: List of Sorry objects to add.
        """
        self.sorries.extend(sorries)

    def write_to_file(self, file_path: Union[str, Path]) -> None:
        """Write the Database to a JSON file.

        Args:
            file_path: Path to the output JSON file.
        """
        # Ensure the directory exists
        path = Path(file_path)
        os.makedirs(path.parent, exist_ok=True)

        # Use Pydantic's model_dump_json to convert to JSON
        json_data = self.model_dump_json(indent=2)

        # Write to the file
        with open(path, "w") as f:
            f.write(json_data)

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> "SorryDatabase":
        """Load a list of Sorry objects from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            A new SorryDatabase instance.
        """
        with open(file_path, "r") as f:
            json_data = f.read()

        # Use Pydantic's model_validate_json to parse the JSON
        return cls.model_validate_json(json_data)
