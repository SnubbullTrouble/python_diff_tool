from sessiondata import SessionData
from dataclasses import asdict, fields
from pathlib import Path
import tomllib
import tomli_w
from typing import Optional


class SessionDataError(Exception):
    """Raised when session data is accessed before being properly loaded."""
    def __init__(self, message: str):
        super().__init__(message)


class Session:
    """
    A singleton class to manage loading and saving session data to a TOML file.
    Automatically creates missing fields as empty strings when loading.
    """
    _instance: Optional["Session"] = None
    SESSION_FILE: str = "session.toml"

    def __new__(cls) -> "Session":
        """
        Ensures only a single instance of Session is created (Singleton pattern).
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._session_data = None
        return cls._instance

    @property
    def session_data(self) -> SessionData:
        """
        Returns the current session data object.

        Raises:
            SessionDataError: If session data has not been loaded yet.
        """
        if self._session_data is None:
            raise SessionDataError("Session data not loaded")
        return self._session_data

    @session_data.setter
    def session_data(self, value: SessionData) -> None:
        """
        Sets the session data manually.

        Args:
            value (SessionData): The session data instance to assign.
        """
        self._session_data = value

    def load_session_data(self, filepath: str = SESSION_FILE) -> SessionData:
        """
        Loads session data from a TOML file. If the file or fields are missing,
        initializes them with empty strings.

        Args:
            filepath (str): Path to the TOML file.

        Returns:
            SessionData: The loaded or default session data object.
        """
        def create_session_with_defaults(loaded_data: Optional[dict] = None) -> SessionData:
            loaded_data = loaded_data or {}
            defaults = {
                field.name: loaded_data.get(field.name, "")
                for field in fields(SessionData)
            }
            return SessionData(**defaults)

        if self._session_data is not None:
            return self._session_data

        if Path(filepath).exists():
            with open(filepath, "rb") as f:
                data = tomllib.load(f)
            self._session_data = create_session_with_defaults(data)
        else:
            self._session_data = create_session_with_defaults()

        return self._session_data

    def save_session_data(self, filepath: str = SESSION_FILE) -> None:
        """
        Saves the current session data to a TOML file.

        Args:
            filepath (str): Path to the TOML file to write.

        Raises:
            SessionDataError: If session data has not been loaded.
        """
        if self._session_data is None:
            raise SessionDataError("No session data to save")

        with open(filepath, "wb") as f:
            tomli_w.dump(asdict(self._session_data), f)
