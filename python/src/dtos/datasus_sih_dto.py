"""
DTO for SIH (Sistema de Informações Hospitalares) DATASUS parameters.
"""


class DatasusSIHDTO:
    """
    Data transfer object for SIH period and state filters.
    """

    def __init__(
        self,
        start_year: str | int | None = None,
        start_month: str | int | None = None,
        end_year: str | int | None = None,
        end_month: str | int | None = None,
        states: str | list[str] | None = None,
    ) -> None:
        self._start_year = start_year
        self._start_month = start_month
        self._end_year = end_year
        self._end_month = end_month
        self._states_raw = self._normalize_states_input(states)

    @staticmethod
    def _normalize_states_input(value: str | list[str] | None) -> str:
        """Store states as comma-separated string."""
        if value is None:
            return ""
        if isinstance(value, list):
            return ",".join(str(s).strip() for s in value if str(s).strip())
        return str(value).strip()

    @property
    def start_year(self) -> str | int | None:
        """Start year of the period (inclusive)."""
        return self._start_year

    @start_year.setter
    def start_year(self, value: str | int | None) -> None:
        self._start_year = value

    @property
    def start_month(self) -> str | int | None:
        """Start month of the period (inclusive)."""
        return self._start_month

    @start_month.setter
    def start_month(self, value: str | int | None) -> None:
        self._start_month = value

    @property
    def end_year(self) -> str | int | None:
        """End year of the period (inclusive)."""
        return self._end_year

    @end_year.setter
    def end_year(self, value: str | int | None) -> None:
        self._end_year = value

    @property
    def end_month(self) -> str | int | None:
        """End month of the period (inclusive)."""
        return self._end_month

    @end_month.setter
    def end_month(self, value: str | int | None) -> None:
        self._end_month = value

    @property
    def states(self) -> list[str]:
        """
        State codes (UF) as a list.
        Parsed from the stored comma-separated string; returns an empty list if empty or not set.
        """
        if not self._states_raw:
            return []
        return [s.strip().upper() for s in self._states_raw.split(",") if s.strip()]

    @states.setter
    def states(self, value: str | list[str] | None) -> None:
        self._states_raw = self._normalize_states_input(value)
