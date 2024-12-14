from typing import List, Optional
from pydantic import BaseModel, Field, validator
import json
from pathlib import Path


class BronzeConfig(BaseModel):
    repo_url: str
    target_path: str
    branch: str = "main"  # Default value
    target_file_types: Optional[List[str]] = None
    sparse: bool = False
    sparse_paths: Optional[List[str]] = None
    data_storage_path: str
    metadata_storage_path: str

    @validator("sparse_paths")
    def validate_sparse_paths(cls, v, values):
        sparse = values.get("sparse", False)
        
        # If sparse is False, sparse_paths should be None or empty
        if not sparse and v:
            raise ValueError("sparse_paths must be None or empty when sparse is False")
        
        # If sparse is True, sparse_paths must exist and not be empty
        if sparse:
            if not v:
                raise ValueError("sparse_paths cannot be empty when sparse is True")
        
        return v

    @validator("repo_url")
    def validate_repo_url(cls, v):
        if not v.endswith(".git"):
            raise ValueError("repo_url must end with .git")
        return v


class ConfigReader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None

    def read_config(self) -> BronzeConfig:
        """
        Read and validate the configuration file.
        
        Returns:
            BronzeConfig: Validated configuration object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            JSONDecodeError: If config file is not valid JSON
            ValidationError: If config doesn't meet the requirements
        """
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config_dict = json.load(f)

        self.config = BronzeConfig(**config_dict)
        return self.config


##########
